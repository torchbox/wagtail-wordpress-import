import os

from django.core.management.base import BaseCommand
from prettytable import PrettyTable

from wagtail_xmlimport.importers.wordpress import WordpressImporter
from wagtail_xmlimport.analysis import HTMLAnalyzer


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("xml_file", type=str, help="The full path to your xml file")
        parser.add_argument(
            "-t",
            "--type",
            type=str,
            help="The wordpress post type/s to import. Use a comma to separate multiple types",
            default="page,post",
        )
        parser.add_argument(
            "-s",
            "--status",
            type=str,
            help="The wordpress post statuse/s to import. Use a comma to separate multiple types",
            default="publish,draft",
        )

    def handle(self, **options):
        xml_file_path = self.get_xml_file(f"{options['xml_file']}")
        importer = WordpressImporter(xml_file_path)
        analyzer = HTMLAnalyzer()

        importer.analyze_html(
            analyzer,
            page_types=options["type"].split(","),
            page_statuses=options["status"].split(","),
        )

        diff_tags = {}

        # Tags
        tags_table = PrettyTable()
        tags_table.field_names = ["Tag", "Pages used on", "Total occurrences"]
        for tag, total_pages in analyzer.tags_unique_pages.most_common():
            diff_tags[tag] = analyzer.tags_total[tag]
            tags_table.add_row([tag, total_pages, analyzer.tags_total[tag]])

        self.stdout.write("Most commonly used HTML tags")
        self.stdout.write(str(tags_table))

        # Attributes
        attributes_table = PrettyTable()
        attributes_table.field_names = ["Tag", "Attribute", "Pages used on", "Total occurrences", "Diff"]
        for (tag, attribute), total_pages in analyzer.attributes_unique_pages.most_common():
            diff = diff_tags[tag] - analyzer.attributes_total[(tag, attribute)]
            attributes_table.add_row([tag, attribute, total_pages, analyzer.attributes_total[(tag, attribute)], diff])

        self.stdout.write("")
        self.stdout.write("Most commonly used HTML attributes. Diff > 0 indicates is missing the attr vs usage")
        self.stdout.write(str(attributes_table))

        # Styles
        styles_table = PrettyTable()
        styles_table.field_names = ["Tag", "Style", "Pages used on", "Total occurrences"]
        for (tag, style), total_pages in analyzer.styles_unique_pages.most_common():
            styles_table.add_row([tag, style, total_pages, analyzer.styles_total[(tag, style)]])

        self.stdout.write("")
        self.stdout.write("Most commonly used inline CSS styles")
        self.stdout.write(str(styles_table))


    def get_xml_file(self, xml_file):
        if os.path.exists(xml_file):
            return xml_file

        self.stdout.write(
            self.style.ERROR(f"The xml file cannot be found at: {xml_file}")
        )
        exit()