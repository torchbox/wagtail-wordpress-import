import sys


class Logger:
    def __init__(self):
        self.processed = 0
        self.imported = 0
        self.skipped = 0
        self.items = []
        self.images = []
        self.urls = []

    # def get_items(self):
    #     return self.items

    # def get_images(self):
    #     return self.images

    # def get_urls(self):
    #     return self.urls

    # def get_processed(self):
    #     return self.processed

    # def get_imported(self):
    #     return self.imported

    # def get_skipped(self):
    #     return self.skipped

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
