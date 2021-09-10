import json

from django.core.management.base import BaseCommand

from wagtail_xmlimport.cls.cls import ImportXml


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("xml_mapping_file", type=str)
        parser.add_argument("--tag", type=str)
        parser.add_argument("--type", type=str)
        parser.add_argument("--status", type=str)

    def handle(self, *args, **options):
        mapping_file_name = options["xml_mapping_file"]
        mapping_file_path = f"model_mappings/{mapping_file_name}"
        mapping = json.load(open(mapping_file_path, "r"))
        importer = ImportXml(
            map_file=mapping, tag=options["tag"], type=options["type"], status=options["status"]
        )
        success, failed = importer.run_import()
        # print(failed)
        # print(success)
        # TODO: we should do some logging here
        # out = ""
        # for item in result:

        #     if item.get("result"):
        #         out += (
        #             str(item.get("result")[0])
        #             + " "
        #             + str(item.get("result")[1])
        #             + " | "
        #         )
        #     else:
        #         out += " EMPTY | "
        # self.stdout.write(self.style.WARNING(out))
