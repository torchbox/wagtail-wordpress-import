import csv

from datetime import datetime


class ProgressManager:
    LOG_DIR = "log"

    processed = []
    skipped = []
    imported = []
    action = []

    def out(self):
        print(
            "Imported:",
            len(self.imported),
            "Processed:",
            len(self.processed),
            "Skipped:",
            len(self.skipped),
        )

    def log_page_action(self, page, result):
        self.action.append((page, result))

    def save_log(self):
        file_name = f"page-action-history-{datetime.now().strftime('%m%d%Y%H%M%S')}.csv"

        log = open(f"{self.LOG_DIR}/{file_name}", "w")
        log_writer = csv.writer(log)
        log_writer.writerow(["id","title","result"])
        for row in self.action:
            log_writer.writerow([row[0].id, row[0].title, row[1]])
