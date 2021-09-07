import json
from datetime import datetime

from django.apps import apps
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from wagtail.core.models import Page

# from wagtail_xmlimport.cls.cls import Mapping

from wagtail_xmlimport.functions import *


def process_date(datestring):
    return make_aware(datetime.strptime(datestring, "%Y-%m-%dT%H:%M:%S"))


def reset_updated_dates(obj, date, revision):
    # update the dates
    obj.first_published_at = date
    obj.last_published_at = date
    obj.latest_revision_created_at = date
    obj.save()
    # rev = obj.save_revision()
    revision.publish()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("mapping_file", type=str)

    def handle(self, *args, **options):
        # self.mapping = Mapping(options["mapping_file"])
        mapping_file_name = options["mapping_file"]
        mapping_file_path = f"model_mappings/{mapping_file_name}"
        mapping_file = open(mapping_file_path, "r")
        self.make_pages(mapping_file)

    def make_pages(self, mapping):
        mapping_data = json.load(mapping)
        mapping_root = mapping_data.get("root")
        xml_file_path = mapping_root.get("file")[0]
        item_tag = mapping_root.get("tag")[0]
        model_name = mapping_root.get("model")[0]

        doc = pulldom.parse(f"xml/{xml_file_path}")

        for event, node in doc:
            if event == pulldom.START_ELEMENT and node.tagName == item_tag:
                doc.expandNode(node)
                dict = node_to_dict(node)
                self.make_page(model_name, dict, mapping_data)

    def make_page(self, model, data, mapping_data):
        home = Page.get_first_root_node().get_children().first()
        page_model = apps.get_model("pages", model)

        values = {}
        date = ""
        # "wp:post_date": ["latest_revision_created_at", "date"]
        for key in mapping_data.keys():
            if isinstance(mapping_data[key], list) and len(mapping_data[key]) >= 1:
                if mapping_data[key][0] == "*date":
                    date = process_date("T".join(data.get(key).split(" ")))
                    # date = v
                # else:
                # TODO do we need to update the date for the past publish, in fact any date in
                # a page model
                v = data.get(key)
                if (
                    len(mapping_data[key]) > 1
                    and mapping_data[key][-1] == "required"
                    and not v
                ):
                    return
                if len(mapping_data[key]) > 1 and not mapping_data[key][-1] == "*date":
                    k = mapping_data[key][0]
                    values[k] = v
                # we have some required fields that have no value in the data
                # TODO log these out

        obj = page_model(**values)
        home.add_child(instance=obj)
        rev = obj.save_revision()
        rev.publish()
        reset_updated_dates(obj, date, rev)
