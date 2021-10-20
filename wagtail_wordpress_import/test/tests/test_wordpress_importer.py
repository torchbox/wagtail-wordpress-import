import os
from django.test import TestCase, override_settings
from wagtail.core.models import Page
from wagtail_wordpress_import.importers.wordpress import WordpressImporter
from wagtail_wordpress_import.logger import Logger
from django.conf import settings

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/fixtures"
LOG_DIR = "fakedir"
IMPORTER_RUN_PARAMS = {
    "app_for_pages": "example",
    "model_for_pages": "TestPage",
    "parent_id": "2",
    "page_types": ["post", "page"],
    "page_statuses": ["publish", "draft"],
}


class WordpressImporterTests(TestCase):
    fixtures = [
        f"{FIXTURES_PATH}/dump.json",
    ]

    def setUp(self):
        self.importer = WordpressImporter(f"{FIXTURES_PATH}/raw_xml.xml")
        self.logger = Logger(LOG_DIR)
        self.importer.run(
            logger=self.logger,
            app_for_pages=IMPORTER_RUN_PARAMS["app_for_pages"],
            model_for_pages=IMPORTER_RUN_PARAMS["model_for_pages"],
            parent_id=IMPORTER_RUN_PARAMS["parent_id"],
            page_types=IMPORTER_RUN_PARAMS["page_types"],
            page_statuses=IMPORTER_RUN_PARAMS["page_statuses"],
        )

        self.parent_page = Page.objects.get(id=IMPORTER_RUN_PARAMS["parent_id"])
        self.imported_pages = self.parent_page.get_children().all()
        self.published_pages = self.parent_page.get_children().live()
        self.draft_pages = self.parent_page.get_children().filter(live=False)

    def test_total_pages_imported(self):
        self.assertEqual(len(self.imported_pages), 2)
        self.assertEqual(len(self.published_pages), 1)
        self.assertEqual(len(self.draft_pages), 1)

    def test_page_field_values(self):
        self.assertEqual(self.published_pages.first().title, "Item one title")
        self.assertEqual(self.published_pages.first().slug, "item-one-title")
        self.assertEqual(
            str(self.published_pages.first().first_published_at.date()), "2010-07-13"
        )
        self.assertEqual(
            str(self.published_pages.first().first_published_at.time()), "16:16:46"
        )
        self.assertEqual(
            str(self.published_pages.first().last_published_at.date()), "2010-07-13"
        )
        self.assertEqual(
            str(self.published_pages.first().last_published_at.time()), "16:16:46"
        )
        self.assertEqual(
            str(self.published_pages.first().latest_revision_created_at.date()),
            "2010-07-13",
        )
        self.assertEqual(
            str(self.published_pages.first().latest_revision_created_at.time()),
            "16:16:46",
        )
        self.assertEqual(
            self.published_pages.first().search_description,
            "This page has a default description",
        )

        # debug fields
        self.assertEqual(self.published_pages.first().specific.wp_post_id, 1)
        self.assertEqual(self.published_pages.first().specific.wp_post_type, "post")
        self.assertEqual(
            self.published_pages.first().specific.wp_link,
            "https://www.example.com/item-one-title/",
        )

        ## these fields are only checked for having some content.
        self.assertTrue(self.published_pages.first().specific.body)
        self.assertTrue(self.published_pages.first().specific.wp_raw_content)
        self.assertTrue(self.published_pages.first().specific.wp_block_json)
        self.assertTrue(self.published_pages.first().specific.wp_processed_content)
        ## this field is not used now but is tested as it should be blank
        ## we can remove this field later if we end up not needing it
        self.assertFalse(self.published_pages.first().specific.wp_normalized_styles)

    def test_logger_totals(self):
        processed = self.logger.processed
        self.assertEqual(processed, 2)

        imported = self.logger.imported
        self.assertEqual(imported, 2)

        skipped = self.logger.skipped
        self.assertEqual(skipped, 0)

    def test_logger_lists(self):
        logger = Logger(LOG_DIR)
        logger.items.append(
            {
                "id": 3,
                "title": "Item one title",
                "link": "https://www.example.com/item-one-title/",
                "result": "updated",
                "reason": "existed",
                "datecheck": "",
                "slugcheck": "",
            }
        )
        logger.items.append(
            {
                "id": 4,
                "title": "Item two title",
                "link": "https://www.example.com/item-two-title/",
                "result": "updated",
                "reason": "existed",
                "datecheck": "",
                "slugcheck": "",
            }
        )

        item_id_3 = next(filter(lambda item: item["id"] == 3, logger.items))
        self.assertEqual(item_id_3["title"], "Item one title")

        item_id_4 = next(filter(lambda item: item["id"] == 4, logger.items))
        self.assertEqual(item_id_4["title"], "Item two title")


@override_settings(WAGTAIL_WORDPRESS_IMPORT_YOAST_PLUGIN_ENABLED=True)
class WordpressImporterTestsOverrideSettings(TestCase):
    fixtures = [
        f"{FIXTURES_PATH}/dump.json",
    ]

    def setUp(self):
        self.importer = WordpressImporter(f"{FIXTURES_PATH}/raw_xml.xml")
        self.logger = Logger(LOG_DIR)
        self.importer.run(
            logger=self.logger,
            app_for_pages=IMPORTER_RUN_PARAMS["app_for_pages"],
            model_for_pages=IMPORTER_RUN_PARAMS["model_for_pages"],
            parent_id=IMPORTER_RUN_PARAMS["parent_id"],
            page_types=IMPORTER_RUN_PARAMS["page_types"],
            page_statuses=IMPORTER_RUN_PARAMS["page_statuses"],
        )

        self.parent_page = Page.objects.get(id=IMPORTER_RUN_PARAMS["parent_id"])
        self.imported_pages = self.parent_page.get_children().all()
        self.published_pages = self.parent_page.get_children().live()
        self.draft_pages = self.parent_page.get_children().filter(live=False)

    def test_page_field_values_with_yoast_plugin_enabled(self):
        self.assertEqual(
            self.published_pages.first().search_description,
            "a search description from yoast for Item one",
        )
