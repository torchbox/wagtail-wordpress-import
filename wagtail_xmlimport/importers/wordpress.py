import json
from xml.dom import pulldom
from wagtail_xmlimport.importers import wordpress_mapping
from wagtail_xmlimport.functions import linebreaks_wp, node_to_dict

from django.apps import apps
from datetime import datetime
from django.utils.timezone import make_aware
from django.utils.text import slugify


class WordpressImporter:
    def __init__(self, xml_file_path):
        self.xml_file = xml_file_path
        self.mapping = wordpress_mapping.mapping
        self.mapping_item = self.mapping.get("item")
        self.mapping_valid_date = self.mapping.get("validate_date")
        self.mapping_valid_slug = self.mapping.get("validate_slug")
        self.mapping_stream_fields = self.mapping.get("stream_fields")
        self.mapping_item_inverse = self.map_item_inverse()
        self.log_processed = 0
        self.log_imported = 0
        self.log_skipped = 0
        self.logged_items = []

    def run(self, *args, **kwargs):
        xml_doc = pulldom.parse(self.xml_file)
        self.page_model_instance = apps.get_model(
            kwargs["app_for_pages"], kwargs["model_for_pages"]
        )
        self.parent_page_obj = (
            apps.get_model(kwargs["app_for_parent"], kwargs["model_for_parent"])
            .get_first_root_node()
            .get_children()
            .first()
        )

        for event, node in xml_doc:
            # each node represents a tag in the xml
            # event is true for the start element
            if event == pulldom.START_ELEMENT and node.tagName == "item":
                xml_doc.expandNode(node)
                item = node_to_dict(node)
                self.log_processed += 1
                if (
                    item.get("wp:post_type") in kwargs["page_types"]
                    and item.get("wp:status") in kwargs["page_statuses"]
                ):

                    # dates_valid and slugs_valid might be useful for 
                    # loging detail
                    item_dict, dates_valid, slugs_valid = self.get_values(item)

                    page_exists = self.page_model_instance.objects.filter(
                        wp_post_id=item.get("wp:post_id")
                    ).first()

                    if page_exists:
                        self.update_page(page_exists, item_dict, item.get("wp:status"))
                        item["log"] = {
                            "result": "updated",
                            "reason": "existed"
                        }
                    else:
                        self.create_page(item_dict, item.get("wp:status"))
                        item["log"] = {
                            "result":"created",
                            "reason": "new"
                        }
                    self.log_imported += 1
                else:
                    item["log"] = {
                        "result": "skipped",
                        "reason": "no title or status match"
                    }
                    self.log_skipped += 1

                print(item.get("title"), item.get("log")["result"])
                self.logged_items.append(item)

        return self.log_imported, self.log_skipped, self.log_processed, self.logged_items

    def create_page(self, values, status):
        obj = self.page_model_instance(**values)

        if status == "draft":
            setattr(obj, "live", False)
        else:
            setattr(obj, "live", True)

        self.parent_page_obj.add_child(instance=obj)

        return obj, "created"

    def update_page(self, page_exists, values, status):
        obj = page_exists

        for key in values.keys():
            setattr(obj, key, values[key])

        obj.save()

        if status == "draft":
            obj.unpublish()

        # self.progress_manager.log_page_action(obj, "updated")

        return obj, "updated"

    def map_item_inverse(self):
        inverse = {}

        for key, value in self.mapping_item.items():
            value = value.split(",")

            if len(value) == 1:
                inverse[value[0]] = key
            else:
                for i in range(len(value)):
                    inverse[value[i]] = key

        return inverse

    def get_values(self, item):
        page_values = {}

        # fields on a page model in wagtail that require a specific input format
        dates_valid = True
        date_fields = self.mapping_valid_date.split(",")

        slugs_valid = True
        slug_fields = self.mapping_valid_slug.split(",")

        stream_fields = self.mapping_stream_fields.split(",")

        for field, mapped in self.mapping_item_inverse.items():
            page_values[field] = item[mapped]

        # stream fields
        for html in stream_fields:
            sfv = self.parse_stream_fields(
                item.get(self.mapping_item_inverse.get(html))
            )
            page_values[html] = sfv

        # dates
        for df in date_fields:
            dt = self.parse_date(item.get(self.mapping_item_inverse.get(df)))
            page_values[df] = dt

        # slugs
        for sf in slug_fields:
            sl = self.parse_slug(
                item.get(self.mapping_item_inverse.get(sf)), item.get("title")
            )
            page_values[sf] = sl

        return page_values, dates_valid, slugs_valid

    def parse_date(self, value):
        if value != "0000-00-00 00:00:00":
            date = "T".join(value.split(" "))
            date_formatted = make_aware(datetime.strptime(date, "%Y-%m-%dT%H:%M:%S"))
            return date_formatted
        return None

    def parse_slug(self, value, title):
        if not value:
            value = title
            print("slug set", title)
        return slugify(value)

    def parse_stream_fields(self, value):
        blocks = []
        blocks.append({"type": "raw_html", "value": linebreaks_wp(value)})
        return json.dumps(blocks)


wordpress_importer_class = WordpressImporter
