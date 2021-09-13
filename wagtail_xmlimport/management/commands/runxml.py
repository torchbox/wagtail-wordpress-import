import json

from django.core.management.base import BaseCommand
from wagtail_xmlimport.cls.progress import ProgressManager
from wagtail_xmlimport.cls.xml_importer import XmlImporter


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("xml_mapping_file", type=str)

    def handle(self, **options):
        mapping_file_path = f"model_mappings/{options['xml_mapping_file']}"
        mapping_json = json.load(open(mapping_file_path, "r"))
        progress = ProgressManager()
        importer = XmlImporter(mapping_json)
        importer.run_import(progress)
        progress.out()
        progress.save_action_log()
        progress.save_skipped_log()
        progress.save_summary_report()
