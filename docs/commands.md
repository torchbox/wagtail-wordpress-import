# Create a command you will run for the import

```
from django.core.management.base import BaseCommand
from wagtail_xmlimport.importers.wordpress import WordpressImporter
from example.home.models import HomePage


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("xml_file", type=str)

    def handle(self, **options):
        xml_file_path = f"{options['xml_file']}"
        importer = WordpressImporter(xml_file_path)
        importer.run("page", "TestPage", HomePage)
        # importer.run("page", "TestPage", HomePage) and one for each page type
```