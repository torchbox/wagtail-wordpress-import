import json

from django.core.management.base import BaseCommand

from wagtail_xmlimport.cls.xml_importer import XmlImporter
from wagtail_xmlimport.cls.progress import ProgressManager


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("xml_mapping_file", type=str)
        # parser.add_argument("--tag", type=str)
        # parser.add_argument("--type", type=str)
        # parser.add_argument("--status", type=str)

    def handle(self, **options):
        mapping_file_path = f"model_mappings/{options['xml_mapping_file']}"
        mapping_json = json.load(open(mapping_file_path, "r"))
        progress = ProgressManager()
        importer = XmlImporter(
            # mapping_json, options["tag"], options["type"], options["status"]
            mapping_json
        )
        importer.run_import(progress)
        progress.out()
        progress.save_log()
