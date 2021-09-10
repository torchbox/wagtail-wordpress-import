class ProgressManager:
    processed = []
    skipped = []
    imported = []

    def out(self):
        print(
            "Imported:",
            len(self.imported),
            "Processed:",
            len(self.processed),
            "Skipped:",
            len(self.skipped),
        )