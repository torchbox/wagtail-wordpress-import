import csv
from datetime import datetime

from django.core.management.base import BaseCommand
from prettytable import PrettyTable

from wagtail_xmlimport.importers.wordpress import WordpressImporter
from wagtail_xmlimport.analysis import HTMLAnalyzer


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("xml_file", type=str)

    def handle(self, **options):
        importer = WordpressImporter(options['xml_file'])
        analyzer = HTMLAnalyzer()

        importer.analyze_html(
            analyzer,
            page_types=["page", "post"],
            page_statuses=["draft", "publish"],
        )

        # Tags
        tags_table = PrettyTable()
        tags_table.field_names = ["Tag", "Pages used on", "Total occurrences"]
        for tag, total_pages in analyzer.tags_unique_pages.most_common():
            tags_table.add_row([tag, total_pages, analyzer.tags_total[tag]])

        self.stdout.write("Most commonly used HTML tags")
        self.stdout.write(str(tags_table))

        # Attributes
        attributes_table = PrettyTable()
        attributes_table.field_names = ["Tag", "Attribute", "Pages used on", "Total occurrences"]
        for (tag, attribute), total_pages in analyzer.attributes_unique_pages.most_common():
            attributes_table.add_row([tag, attribute, total_pages, analyzer.attributes_total[(tag, attribute)]])

        self.stdout.write("")
        self.stdout.write("Most commonly used HTML attributes")
        self.stdout.write(str(attributes_table))

        # Styles
        styles_table = PrettyTable()
        styles_table.field_names = ["Tag", "Style", "Pages used on", "Total occurrences"]
        for (tag, style), total_pages in analyzer.styles_unique_pages.most_common():
            styles_table.add_row([tag, style, total_pages, analyzer.styles_total[(tag, style)]])

        self.stdout.write("")
        self.stdout.write("Most commonly used inline CSS styles")
        self.stdout.write(str(styles_table))

