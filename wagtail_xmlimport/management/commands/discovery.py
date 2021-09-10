import json
import os

from django.core.management.base import BaseCommand
from wagtail_xmlimport.cls.util import PathsToDict


class Command(BaseCommand):

    help = """Utils to output xml structure to a json file."""

    def __init__(self, *args, **kwargs):
        self.xml_folder_path = "xml"
        self.json_folder_path = "json"
        if not os.path.exists(self.json_folder_path):
            os.makedirs(self.json_folder_path)
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument("xmlfile", type=str)

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Parsing ..."))
        self.stdout.write(
            self.style.NOTICE(
                "If this is a large file and has many depths it will take some time to complete"
            )
        )
        file_name = options["xmlfile"]
        xml = open(f"{self.xml_folder_path}/{file_name}", "rb").read()

        json_file_name = file_name.split(".")[0]
        json_file = open(f"{self.json_folder_path}/{json_file_name}.json", "w+")

        paths_dict = PathsToDict(xml).get_dict()

        json_file.write(json.dumps(paths_dict, indent=2))

        self.stdout.write(
            self.style.SUCCESS(f"Finished Your file is here: {json_file_name}.json")
        )
