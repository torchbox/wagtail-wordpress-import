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

    def log_page_action(self, page, result): # on successful page creation only
        self.action.append((page, result))

    def save_action_log(self): 
        file_name = f"page-action-history-{datetime.now().strftime('%m%d%Y%H%M%S')}.csv"

        log = open(f"{self.LOG_DIR}/{file_name}", "w")
        log_writer = csv.writer(log)
        log_writer.writerow(["id","title","result"])
        for row in self.action:
            log_writer.writerow([row[0].id, row[0].title, row[1]])

    def log_page_skipped(self, item, reason, key):
        # prime the row
        item["reason"] = reason
        item["key"] = key
        item["content:encoded"] = "intentionally removed to help with csv formatting"
        # temporary measure while not dealing with category
        if not "category" in item.keys():
            item["category"] = ""
        self.skipped.append(item)

    def save_skipped_log(self): 
        # the order of the keys may matter going forward
        file_name = f"page-skipped-history-{datetime.now().strftime('%m%d%Y%H%M%S')}.csv"
        log = open(f"{self.LOG_DIR}/{file_name}", "w")
        log_writer = csv.DictWriter(log, self.skipped[0].keys())
        log_writer.writeheader()
        for row in self.skipped:
            log_writer.writerow(row)
            

    def save_summary_report(self):
        file_name = f"summary-{datetime.now().strftime('%m%d%Y%H%M%S')}.txt"
        processed = f"Items processed: {len(self.processed)}"
        skipped = f"Items skipped: {len(self.skipped)}"
        imported = f"Items imported: {len(self.imported)}"

        out = f"Import Summary\n============== \n{processed}\n{skipped}\n{imported}" 
        log = open(f"{self.LOG_DIR}/{file_name}", "w")
        log.write(out)