import csv
import os
from datetime import datetime

from django.core.management.base import BaseCommand
from wagtail_wordpress_import.importers.wordpress import WordpressImporter
from wagtail_wordpress_import.logger import Logger

LOG_DIR = "log"


class Command(BaseCommand):
    help = """Run the import process on all items in the XML file and make 
    them child pages of a specific page."""

    """
    ./manage.py import_xml parent_page_id [--app] [--model] [--type] [--status]

    The default is:
    Import all `post` and `page` types of status `draft` and `publish` as children
    of the page with id of parent_id
    """

    def add_arguments(self, parser):
        parser.add_argument("xml_file", type=str, help="The full path to your xml file")
        parser.add_argument(
            "parent_id",
            type=int,
            help="The page ID of the parent page to use when creating imported pages",
        )
        parser.add_argument(
            "-a",
            "--app",
            type=str,
            help="The app which contains your page models for the import",
            default="pages",
        )
        parser.add_argument(
            "-m",
            "--model",
            type=str,
            help="The page model to use for the imported pages",
            default="PostPage",
        )
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
        logger = Logger()
        importer = WordpressImporter(xml_file_path)
        logged_items = importer.run(
            page_types=options["type"].split(","),
            page_statuses=options["status"].split(","),
            app_for_pages=options["app"],
            model_for_pages=options["model"],
            parent_id=options["parent_id"],
            logger=logger,
        )
        logger.output_import_summary()
        self.save_csv_files(logged_items)
        # print(logger.__dict__)

    def get_xml_file(self, xml_file):
        if os.path.exists(xml_file):
            return xml_file

        self.stdout.write(
            self.style.ERROR(f"The xml file cannot be found at: {xml_file}")
        )
        exit()

    # def summary(self, logger):
    #     self.stdout.write(self.style.WARNING("Summary ========================"))
    #     self.stdout.write(
    #         "Imported: "
    #         + str(logger.imported)
    #         + " Skipped: "
    #         + str(logger.skipped)
    #         + " Processed: "
    #         + str(logger.processed)
    #     )
    #     if logger.processed - logger.skipped == logger.imported:
    #         self.stdout.write(self.style.SUCCESS("Success"))
    #     else:
    #         self.stdout.write(self.style.ERROR("Error"))

    def save_csv_files(self, logged):
        file_name = (
            f"{LOG_DIR}/import-results-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
        )

        with open(file_name, "w", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=[
                    "id",
                    "title",
                    "url",
                    "reason",
                    "result",
                    "dates",
                    "slug",
                ],
            )
            writer.writerow(
                {
                    "id": "Page ID",
                    "title": "Page Title",
                    "url": "Wordpress Link",
                    "reason": "Reason for result ->",
                    "result": "Result",
                    "dates": "Dates Changed",
                    "slug": "Slug Changed",
                }
            )
            for row in logged["items"]:
                writer.writerow(
                    {
                        "id": row["id"],
                        "title": row["title"],
                        "url": row["link"],
                        "reason": row["reason"],
                        "result": row["result"],
                        "dates": row["datecheck"],
                        "slug": row["slugcheck"],
                    }
                )
