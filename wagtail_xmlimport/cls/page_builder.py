import json

from django.apps import apps
from django.utils.text import slugify
from django.utils.timezone import make_aware
from datetime import datetime

from wagtail_xmlimport.functions import linebreaks_wp

# TODO: doesn't seem right that this needs to happen
# how can save on firt save?
# def reset_dates(obj, values, published):
#     # update the dates
#     obj.first_published_at = values.get("first_published_at")
#     obj.last_published_at = values.get("last_published_at")
#     obj.latest_revision_created_at = values.get("latest_revision_created_at")
#     if published:
#         obj.save()
#     else:
#         obj.unpublish()
#     # revision.publish()


class PageBuilder:
    def __init__(self, item, model, mapping, site_root_page, progress_manager):
        self.item = item
        self.model = model
        self.mapping = mapping
        self.values = {}
        self.site_root_page = site_root_page
        # self.skipped = []
        self.progress_manager = progress_manager

    def run(self):
        # self.result = result
        # statuses = self.mapping.get("root")["status"]
        # if self.item.get("status") not in statuses:
        # page, result = self.parse_item(self.model, self.item, self.mapping)
        return self.parse_item(self.model, self.item, self.mapping)

    def parse_item(self, model, item, mapping):
        self.page_model = apps.get_model("pages", model)

        # mapping keys are json file keys
        # not interested in the root key
        # values of interest are keys of length > 0
        # we only need to parse items that have one of the statuses

        for key in mapping.keys():

            if isinstance(mapping[key], list) and len(mapping[key]):
                # are there any required fields without a value?
                # don't continue
                if "required" in mapping[key] and not item[key]:
                    self.progress_manager.skipped.append(item)
                    continue

                # handle meta like status
                if "__" in mapping[key][0] and mapping[key][0].index("__") == 0:
                    if mapping[key][0] == "__status":
                        self.status = item.get(key)

                # handle everything expect dates and page meta like status
                if not "%%" in mapping[key][0] and not "__" in mapping[key][0]:
                    field_value_parser = PageFieldValueParser()
                    item_value = field_value_parser.parse_field_value(
                        field_name=mapping[key][0],
                        value=item.get(key),
                        other=mapping[key],
                    )
                    self.values[mapping[key][0]] = item_value

                # handle dates
                if "%%" in mapping[key][0] and mapping[key][0].index("%%") == 0:
                    # deal with dates
                    field_value_parser = PageFieldValueParser()
                    extra_fields = None
                    if len(mapping[key]) == 2:
                        extra_fields = mapping[key][1]
                    item_value = field_value_parser.parse_field_value(
                        field_name=mapping[key][0].replace("%%", ""),
                        value=item.get(key),
                        other=False,
                        extra_fields=extra_fields,
                    )

                    for k, v in item_value.items():
                        self.values[k] = v

        if self.status in self.mapping["root"]["status"]:

            self.progress_manager.imported.append(item)

            page_exists = self.page_model.objects.filter(
                wp_post_id=self.values.get("wp_post_id")
            ).first()

            if not page_exists:
                page, result = self.make_page()
                return page, result

            page, result = self.update_page(page_exists)
            return page, result

    def make_page(self):
        obj = self.page_model(**self.values)

        self.site_root_page.add_child(instance=obj)

        obj.save_revision().publish()

        setattr(obj, "first_published_at", self.values.get("first_published_at"))
        setattr(obj, "last_published_at", self.values.get("last_published_at"))
        setattr(obj, "latest_revision_created_at", self.values.get("latest_revision_created_at"))
        setattr(obj, "has_unpublished_changes", False)

        obj.save()

        if self.status == "draft":
            obj.unpublish()

        return obj, "created"

    def update_page(self, page):
        obj = self.page_model.objects.get(pk=page)

        for key in self.values.keys():
            setattr(obj, key, self.values[key])

        if self.status == "draft":
            setattr(obj, "live", False)
        else:
            setattr(obj, "live", True)

        # obj.save_revision().publish()

        setattr(obj, "first_published_at", self.values.get("first_published_at"))
        setattr(obj, "last_published_at", self.values.get("last_published_at"))
        setattr(obj, "latest_revision_created_at", self.values.get("latest_revision_created_at"))
        setattr(obj, "has_unpublished_changes", True)

        obj.save_revision().publish()

        setattr(obj, "first_published_at", self.values.get("first_published_at"))
        setattr(obj, "last_published_at", self.values.get("last_published_at"))
        setattr(obj, "latest_revision_created_at", self.values.get("latest_revision_created_at"))
        setattr(obj, "has_unpublished_changes", False)

        obj.save()

        if self.status == "draft":
            obj.unpublish()

        return obj, "updated"


class PageFieldValueParser:
    def parse_field_value(self, field_name, value, other=None, extra_fields=None):
        if field_name == "title":
            return self.parse_title(value, other)

        if field_name == "body":
            return self.parse_body(value, other)

        if field_name == "wp_post_id":
            return self.parse_wp_post_id(value, other)

        if field_name == "wp_post_type":
            return self.parse_wp_post_type(value, other)

        if field_name == "slug":
            return self.parse_body(value, other)

        if field_name == "date":
            return self.parse_date(value, other, extra_fields)

        # if field_name == "status":
        #     print(value)
            # return self.parse_date(value, other, extra_fields)

    def parse_title(self, value, other):
        if other == "required" and not value:
            return None
        return value

    def parse_body(self, value, other):
        if "body" in other:
            return self.make_stream_blocks(value, other)

    def parse_wp_post_id(self, value, other):
        return value

    def parse_wp_post_type(self, value, other):
        return value

    def parse_slug(self, value, other):
        if "slug" in other:
            return slugify(value)

    def parse_date(self, value, other, extra_fields):
        if other == "required" and not value:
            return None
        extra_fields = extra_fields.split(":")
        date = "T".join(value.split(" "))
        date_formatted = make_aware(datetime.strptime(date, "%Y-%m-%dT%H:%M:%S"))
        ret = {}
        for field in extra_fields:
            ret[field] = date_formatted

        return ret

    def make_stream_blocks(self, value, other):
        pipes = []
        if len(other) > 1 and "stream" in other[1]:
            pipes = other[1].split(":")

        if "*auto_p" in pipes:
            value = linebreaks_wp(value)

        blocks = [{"type": "raw_html", "value": value}]
        return json.dumps(blocks)