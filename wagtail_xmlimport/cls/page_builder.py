import json
from datetime import datetime

from bs4 import BeautifulSoup as bs
from django.apps import apps
from django.utils.text import slugify
from django.utils.timezone import make_aware
from wagtail_xmlimport.functions import linebreaks_wp


class PageBuilder:
    def __init__(
        self, item, model, mapping, site_root_page, progress_manager, type, app
    ):
        self.item = item
        self.model = model
        self.mapping = mapping
        self.values = {}
        self.site_root_page = site_root_page
        self.type = type
        self.app = app
        self.progress_manager = progress_manager
        # print("builder")

    def run(self):
        return self.parse_item(self.model, self.item, self.mapping, self.type, self.app)

    # TODO: type is unsed need to investigate
    def parse_item(self, model, item, mapping, type, app):
        self.page_model = apps.get_model(app, model)

        # 'mapping' keys are json file keys
        # values of interest are keys of length > 0
        # we only need to parse items that have one of the statuses
        # print(item)
        # exit()

        for key in mapping.keys():

            if isinstance(mapping[key], list) and len(mapping[key]):

                # are there any required fields without a value?
                # don't continue
                if "required" in mapping[key] and not item[key]:
                    self.progress_manager.skipped.append(item)
                    continue

                # handle meta like status
                elif "__" in mapping[key][0] and mapping[key][0].index("__") == 0:
                    if mapping[key][0] == "__status":
                        self.status = item.get(key)

                # handle dates
                elif "%%" in mapping[key][0] and mapping[key][0].index("%%") == 0:
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

                # handle everything else. just for now need to catch stuff
                elif not "%%" in mapping[key][0] and not "__" in mapping[key][0]:
                    field_value_parser = PageFieldValueParser()
                    item_value = field_value_parser.parse_field_value(
                        field_name=mapping[key][0],
                        value=item.get(key),
                        other=mapping[key],
                    )
                    # getting back various field types here
                    # counld be a stream field too whcih would be a json.dumps
                    # of stream blocks
                    self.values[mapping[key][0]] = item_value

                # some other value
                else:
                    print(f"dont know how to handle this item: {item.get('title')}")

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

    """
    TODO: I think we may need more discussion around page updating after an initial import
    Thinking this. The import is really only a snapshot in time at the last import.

    First import 
        OK and the published/updated dates are all set OK. The page is live without any history other
        than this create action.

    Subsequent Imports
        Not checking to see which data has changed (could be complicated)
        Currently restetting all data from the previous import to the current data whcih could have changes.
        If the data has changed the only peice we know about is updated dates, publish staus whcih gets updated.
        If a pages is saved here bexuse it may have chenages then the page needs to be published again to reflect
        that in wagtail. The updated data is now not the imported date but the moment we update it on this import

    To Keep Page History Intact
        If we are updating previous imported pages with potential new data we need to maintain the history.
    Dump The History
        This is how it is currently working.

    """

    def make_page(self):
        obj = self.page_model(**self.values)

        if self.status == "draft":
            setattr(obj, "live", False)
        else:
            setattr(obj, "live", True)

        self.site_root_page.add_child(instance=obj)

        self.progress_manager.log_page_action(obj, "created")

        return obj, "created"

    def update_page(self, page):
        obj = self.page_model.objects.get(pk=page)

        for key in self.values.keys():
            setattr(obj, key, self.values[key])

        obj.save()

        if self.status == "draft":
            obj.unpublish()

        self.progress_manager.log_page_action(obj, "updated")

        return obj, "updated"


class PageFieldValueParser:
    def parse_field_value(self, field_name, value, other=None, extra_fields=None):

        just_return = ["title", "wp_post_id", "wp_post_type"]

        if field_name in just_return:
            return value

        elif field_name == "slug":
            return self.parse_slug(value, other)

        elif field_name == "date":
            return self.parse_date(value, other, extra_fields)

        elif field_name == "body":
            return self.parse_body(value, other)

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

    def parse_body(self, value, other):
        if "stream" in other[1]:
            return self.make_stream_blocks(value, other)
        else:
            return value

    def make_stream_blocks(self, value, other):

        pf = PreFilterHtml()
        pf.set_value(value)

        if "*auto_p" in other[1].split(":"):
            pf.auto_p()

        # just testing bs4
        # pf.beautiful_soup()
        # print(f"#p tags: \n{len(pf.soup.findAll('p'))}\n")
        return pf.get_blocks("raw_html", False)


class PreFilterHtml:
    def __init__(self, blocks=None):
        self.blocks = []
        if blocks:
            self.blocks = blocks

    def set_value(self, value):
        self.value = value

    def set_initial_blocks(self, blocks):
        self.blocks = blocks

    def auto_p(self):
        self.value = linebreaks_wp(self.value)

    def raw_html_block(self):
        self.blocks.append({"type": "raw_html", "value": self.value})

    def rich_text_block(self):
        self.blocks.append({"type": "rich_text", "value": self.value})

    def get_blocks(self, single, generate):
        if single:
            getattr(self, f"{single}_block")()
        elif generate:
            self.auto_generate()

        return json.dumps(self.blocks)

    def beautiful_soup(self):
        self.soup = bs(self.value)
        # print(len(self.soup))

    def auto_generate(self):
        pass
