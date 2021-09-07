import json
from django.core.management.base import BaseCommand
from wagtail_xmlimport.cls.cls import ImportXml

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("xml_mapping_file", type=str)

    def handle(self, *args, **options):
        mapping_file_name = options["xml_mapping_file"]
        mapping_file_path = f"model_mappings/{mapping_file_name}"
        mapping = json.load(open(mapping_file_path, "r"))
        importer = ImportXml(mapping)
        ran = importer.run_import()
        print(ran)