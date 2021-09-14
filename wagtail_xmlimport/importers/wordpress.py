import json
from copy import copy
from xml.dom import pulldom
from wagtail_xmlimport.importers import wordpress_mapping
from wagtail_xmlimport.functions import linebreaks_wp, node_to_dict

from wagtail_xmlimport.cls.page_maker import PageMaker
from wagtail_xmlimport.cls.progress import ProgressManager
from django.apps import apps
from datetime import datetime
from django.utils.timezone import make_aware
from django.utils.text import slugify


class WordpressImporter:
    def __init__(self, xml_file_path):
        self.xml_file = xml_file_path
        self.mapping = wordpress_mapping.mapping
        self.mapping_root = self.mapping.get("root")
        self.mapping_item = self.mapping.get("item")
        self.mapping_valid_date = self.mapping.get("validate_date")
        self.mapping_valid_slug = self.mapping.get("validate_slug")
        self.mapping_stream_fields = self.mapping.get("stream_fields")
        self.mapping_item_inverse = self.map_item_inverse()
        self.progress_manager = ProgressManager()

    def run(self, *args, **kwargs):
        xml_doc = pulldom.parse(self.xml_file)
        tag = self.mapping_root.get("tag")
        self.page_model_instance = apps.get_model(
            kwargs["app_for_pages"], kwargs["model_for_pages"]
        )
        self.parent_page_obj = (
            apps.get_model(kwargs["app_for_parent"], kwargs["model_for_parent"])
            .get_first_root_node()
            .get_children()
            .first()
        )

        print("⏳ working ...", end="\r")

        for event, node in xml_doc:
            # each node represents a tag in the xml
            # event is true for the start element
            if event == pulldom.START_ELEMENT and node.tagName == tag:
                xml_doc.expandNode(node)
                item = node_to_dict(node)

                if item.get("wp:post_type") and item.get(
                    "wp:post_type"
                ) == self.mapping_root.get("type"):

                    item_dict, dates_valid, slugs_valid = self.get_values(item)

                    # TODO: do some checking of alid above
                    page_exists = self.page_model_instance.objects.filter(
                        wp_post_id=item.get("wp:post_id")
                    ).first()

                    if page_exists:
                        self.update_page(page_exists, item_dict, item.get("wp:status"))
                    else:
                        self.create_page(item_dict, item.get("wp:status"))

                    # return item_dict

    def page_exists(self, item):
        return self.page_model_instance.objects.filter(
            wp_post_id=item.get("wp:post_id")
        ).first()

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
            sfv = self.parse_stream_fields(item.get(self.mapping_item_inverse.get(html)))
            page_values[html] = sfv

        # dates
        for df in date_fields:
            dt = self.parse_date(item.get(self.mapping_item_inverse.get(df)))
            page_values[df] = dt

        # slugs
        for sf in slug_fields:
            sl = self.parse_slug(item.get(self.mapping_item_inverse.get(sf)))
            page_values[sf] = sl

        return page_values, dates_valid, slugs_valid

    def parse_date(self, value):
        if value != "0000-00-00 00:00:00":
            date = "T".join(value.split(" "))
            date_formatted = make_aware(datetime.strptime(date, "%Y-%m-%dT%H:%M:%S"))
            return date_formatted
        return None

    def parse_slug(self, value):
        return slugify(value)

    def parse_stream_fields(self, value):
        blocks = []
        blocks.append({"type": "raw_html", "value": linebreaks_wp(value)})
        # pf = PreFilterHtml()
        # pf.set_value(value)

        # if "*auto_p" in other[1].split(":"):
        #     pf.auto_p()

        # just testing bs4
        # pf.beautiful_soup()
        # print(f"#p tags: \n{len(pf.soup.findAll('p'))}\n")
        return json.dumps(blocks)


wordpress_importer_class = WordpressImporter
