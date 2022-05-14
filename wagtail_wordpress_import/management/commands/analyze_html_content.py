import os

from django.core.management.base import BaseCommand
from prettytable import PrettyTable

from wagtail_wordpress_import.analysis import HTMLAnalyzer
from wagtail_wordpress_import.importers.wordpress import WordpressImporter


class Command(BaseCommand):
    help = """This command is not used directly in an import.

    It's a tool to help you see and understand the html tags in the content as well as the inline styles found.

    It ouputs a series of tables to the command line.
    The ouput is ideally used inside a spreadsheet by piping it out to a file and importing it.
    Hint: Use the | as a column separator when importing

    Use a command like: ./manage.py analyze_html_content [your_source_xml_file] > analysis.txt
    Then remove the titles and horizontal table lines so it looks like:

    |    Tag     | Pages used on | Total occurrences |
    |     p      |      2504     |       41696       |
    |     a      |      2433     |       19646       |
    |   strong   |      2147     |       21020       |
    ...

    and save each table to a separate file for later import.
    """

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

        # Tags
        tags_table = PrettyTable()
        tags_table.field_names = ["Tag", "Pages used on", "Total occurrences"]
        for tag, total_pages in analyzer.tags_unique_pages.most_common():
            tags_table.add_row([tag, total_pages, analyzer.tags_total[tag]])

        self.stdout.write("Most commonly used HTML tags")
        self.stdout.write(str(tags_table))

        # Attributes
        attributes_table = PrettyTable()
        attributes_table.field_names = [
            "Tag",
            "Attribute",
            "Pages used on",
            "Total occurrences",
        ]
        for (
            tag,
            attribute,
        ), total_pages in analyzer.attributes_unique_pages.most_common():
            attributes_table.add_row(
                [
                    tag,
                    attribute,
                    total_pages,
                    analyzer.attributes_total[(tag, attribute)],
                ]
            )

        self.stdout.write("")
        self.stdout.write("Most commonly used HTML attributes.")
        self.stdout.write(str(attributes_table))

        # Styles
        styles_table = PrettyTable()
        styles_table.field_names = [
            "Tag",
            "Style",
            "Pages used on",
            "Total occurrences",
        ]
        for (tag, style), total_pages in analyzer.styles_unique_pages.most_common():
            styles_table.add_row(
                [tag, style, total_pages, analyzer.styles_total[(tag, style)]]
            )

        self.stdout.write("")
        self.stdout.write("Most commonly used inline CSS styles")
        self.stdout.write(str(styles_table))

        shortcodes_table = PrettyTable()
        shortcodes_table.field_names = [
            "Shortcode",
            "Pages used on",
            "Total occurrences",
        ]
        for shortcode, total_pages in analyzer.shortcodes_unique_pages.most_common():
            shortcodes_table.add_row(
                [shortcode, total_pages, analyzer.shortcodes_total[shortcode]]
            )

        self.stdout.write("Most commonly used shortcodes")
        self.stdout.write(str(shortcodes_table))

    def get_xml_file(self, xml_file):
        if os.path.exists(xml_file):
            return xml_file

        self.stdout.write(
            self.style.ERROR(f"The xml file cannot be found at: {xml_file}")
        )
        exit()
