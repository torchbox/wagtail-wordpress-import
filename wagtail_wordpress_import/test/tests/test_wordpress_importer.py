import os
from django.test import TestCase
from wagtail_wordpress_import.importers.wordpress import WordpressImporter

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/fixtures"


class WordpressImporterTests(TestCase):
    def setUp(self):
        self.importer = WordpressImporter(f"{FIXTURES_PATH}/test.xml")

    def test_importer_class(self):
        self.assertIsInstance(self.importer, WordpressImporter)

    def test_importer_init(self):
        self.assertEqual(self.importer.logged_items["processed"], 0)
        self.assertEqual(self.importer.logged_items["imported"], 0)
        self.assertEqual(self.importer.logged_items["skipped"], 0)
        self.assertIsInstance(self.importer.logged_items["items"], list)
