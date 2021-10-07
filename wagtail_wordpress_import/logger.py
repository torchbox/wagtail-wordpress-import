import sys
import csv
from datetime import datetime


class Logger:
    def __init__(self, logdir):
        self.logdir = logdir
        self.processed = 0
        self.imported = 0
        self.skipped = 0
        self.items = []
        self.images = []
        self.urls = []

    def log_progress(self):
        item = self.items[-1]
        if not item["id"] == 0:
            sys.stdout.write(
                f"{item['id']}, {item['title']}, {item['result']}, {self.processed}\n"
            )
        else:
            sys.stdout.write(f"skipped ... {self.processed}\n")

    def get_items_report_data(self):
        report_data = {
            "processed": self.processed,
            "imported": self.imported,
            "skipped": self.skipped,
            "items": self.items,
        }

        return report_data

    def output_import_summary(self):
        sys.stdout.write("Summary ========================")
        sys.stdout.write(
            "\nImported: "
            + str(self.imported)
            + " Skipped: "
            + str(self.skipped)
            + " Processed: "
            + str(self.processed)
        )
        if self.processed - self.skipped == self.imported:
            sys.stdout.write("\n✅ Completed Successfully\n")
        else:
            sys.stdout.write(
                "\n⚠️ Completed but there were errors with imported amounts\n"
            )

    def save_csv_import_report(self):
        file_name = f"{self.logdir}/import-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"

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
            for row in self.items:
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

    def save_csv_images_report(self):
        pass

    def save_csv_urls_report(self):
        pass
