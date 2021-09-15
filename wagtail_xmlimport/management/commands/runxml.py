import csv

from datetime import datetime

from django.core.management.base import BaseCommand
from wagtail_xmlimport.importers.wordpress import WordpressImporter

LOG_DIR = "log"


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("xml_file", type=str)

    def handle(self, **options):
        xml_file_path = f"{options['xml_file']}"
        importer = WordpressImporter(xml_file_path)
        imported, skipped, processed, logged = importer.run(
            page_types=["page", "post"],  # the word press page type
            page_statuses=["draft", "publish"],
            app_for_pages="pages",
            model_for_pages="PostPage",
            app_for_parent="home",
            model_for_parent="HomePage",
        )
        self.summary(imported, skipped, processed)
        self.save_csv_files(logged)

    def summary(self, imported, skipped, processed):
        self.stdout.write(self.style.WARNING("Summary ========================"))
        self.stdout.write(
            "Imported: "
            + str(imported)
            + " Skipped: "
            + str(skipped)
            + " Processed: "
            + str(processed)
        )
        calc = processed - skipped == imported
        if calc:
            self.stdout.write(self.style.SUCCESS(f"Check: {calc}"))
        else:
            self.stdout.write(self.style.ERROR()(f"Check: {calc}"))

    def save_csv_files(self, logged):
        file_name = (
            f"{LOG_DIR}/import-history-{datetime.now().strftime('%m%d%Y%H%M%S')}.csv"
        )

        with open(file_name, "w", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=["id", "title", "url", "reason", "result"]
            )
            writer.writeheader()
            for row in logged:
                writer.writerow(
                    {
                        "id": row["wp:post_id"],
                        "title": row["title"],
                        "url": row["link"],
                        "reason": row["log"]["reason"],
                        "result": row["log"]["result"],
                    }
                )
