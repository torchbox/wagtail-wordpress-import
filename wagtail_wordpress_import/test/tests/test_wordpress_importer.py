import os

from django.test import TestCase
from wagtail_wordpress_import.importers.wordpress import WordpressImporter
from wagtail_wordpress_import.logger import Logger

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/fixtures"
LOG_DIR = "fakedir"


class WordpressImporterTests(TestCase):
    fixtures = [
        f"{FIXTURES_PATH}/dump.json",
    ]

    def setUp(self):
        self.importer = WordpressImporter(f"{FIXTURES_PATH}/raw_xml.xml")
        self.logger = Logger(LOG_DIR)
        self.importer.run(
            logger=self.logger,
            app_for_pages="example",
            model_for_pages="TestPage",
            parent_id="2",
            page_types=["post", "page"],
            page_statuses=["publish", "draft"],
        )

    def test_importer_class(self):
        self.assertIsInstance(self.importer, WordpressImporter)

    def test_importer_init(self):
        self.assertEqual(self.importer.xml_file, f"{FIXTURES_PATH}/raw_xml.xml")

    def test_logger_totals(self):
        logdir = self.logger.logdir
        self.assertEqual(logdir, "fakedir")

        processed = self.logger.processed
        self.assertEqual(processed, 2)

        imported = self.logger.imported
        self.assertEqual(imported, 2)

        skipped = self.logger.skipped
        self.assertEqual(skipped, 0)

        # item_id_3 = {}
        # for item in self.logger.items:
        #     if item["id"] == 3:
        #         item_id_3 = item
        # self.assertEqual(item_id_3["title"], "Item one title")

        # item_id_4 = {}
        # for item in self.logger.items:
        #     if item["id"] == 4:
        #         item_id_4 = item
        # self.assertEqual(item_id_4["title"], "Item two title")

        # images = self.logger.images
        # self.assertEqual(len(images), 0)  # TODO no data for this yet, temp test

        # urls = self.logger.urls
        # self.assertEqual(len(urls), 0)  # TODO no data for this yet, temp test

        # page_link_errors = self.logger.page_link_errors
        # self.assertEqual(
        #     len(page_link_errors), 2
        # )  # TODO no data for this yet, temp test
