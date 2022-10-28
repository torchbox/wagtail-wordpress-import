import os

from django.test import TestCase, override_settings
from wagtail import VERSION as WAGTAIL_VERSION

if WAGTAIL_VERSION >= (3, 0):
    from wagtail.models import Page
else:
    from wagtail.core.models import Page

from wagtail_wordpress_import.importers.wordpress import WordpressImporter
from wagtail_wordpress_import.logger import Logger

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/fixtures"
LOG_DIR = "fakedir"
IMPORTER_RUN_PARAMS_TEST = {
    "app_for_pages": "wagtail_wordpress_import_test",
    "model_for_pages": "TestPage",
    "parent_id": "2",
    "page_types": ["post", "page"],
    "page_statuses": ["publish", "draft"],
}


@override_settings(WAGTAIL_WORDPRESS_IMPORTER_SOURCE_DOMAIN="http://www.example.com")
class WordpressImporterTests(TestCase):
    fixtures = [
        f"{FIXTURES_PATH}/dump.json",
    ]

    def setUp(self):
        self.importer = WordpressImporter(f"{FIXTURES_PATH}/raw_xml.xml")
        self.logger = Logger(LOG_DIR)
        self.importer.run(
            logger=self.logger,
            app_for_pages=IMPORTER_RUN_PARAMS_TEST["app_for_pages"],
            model_for_pages=IMPORTER_RUN_PARAMS_TEST["model_for_pages"],
            parent_id=IMPORTER_RUN_PARAMS_TEST["parent_id"],
            page_types=IMPORTER_RUN_PARAMS_TEST["page_types"],
            page_statuses=IMPORTER_RUN_PARAMS_TEST["page_statuses"],
        )

        self.parent_page = Page.objects.get(id=IMPORTER_RUN_PARAMS_TEST["parent_id"])
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

        # these fields are only checked for having some content.
        self.assertTrue(self.published_pages.first().specific.body)
        self.assertTrue(self.published_pages.first().specific.wp_raw_content)
        self.assertTrue(self.published_pages.first().specific.wp_block_json)
        self.assertTrue(self.published_pages.first().specific.wp_processed_content)
        # this field is not used now but is tested as it should be blank
        # we can remove this field later if we end up not needing it
        self.assertFalse(self.published_pages.first().specific.wp_normalized_styles)

    def test_logger_totals(self):
        processed = self.logger.processed
        self.assertEqual(processed, 5)

        imported = self.logger.imported
        self.assertEqual(imported, 2)

        skipped = self.logger.skipped
        self.assertEqual(skipped, 3)

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

    def test_page_field_values_with_yoast_plugin_disbaled(self):
        self.assertEqual(
            self.published_pages.first().search_description,
            "This page has a default description",
        )

    def test_page_field_values_if_no_post_date_modified(self):
        page = self.imported_pages.get(title="Item two title")
        print(page)
        self.assertEqual(str(page.first_published_at.date()), "2010-01-13")
        self.assertEqual(str(page.first_published_at.time()), "16:00:00")
        self.assertEqual(str(page.last_published_at.date()), "2010-01-13")
        self.assertEqual(str(page.last_published_at.time()), "16:00:00")
        self.assertEqual(
            str(page.latest_revision_created_at.date()),
            "2010-01-13",
        )
        self.assertEqual(
            str(page.latest_revision_created_at.time()),
            "16:00:00",
        )


IMPORTER_RUN_PARAMS_TEST_OVERRIDE_1 = {
    "app_for_pages": "wagtail_wordpress_import_test",
    "model_for_pages": "TestPage",
    "parent_id": "2",
    "page_types": ["post"],
    "page_statuses": ["publish", "draft"],
}


@override_settings(
    WAGTAIL_WORDPRESS_IMPORT_YOAST_PLUGIN_ENABLED=True,
    WAGTAIL_WORDPRESS_IMPORTER_SOURCE_DOMAIN="http://www.example.com",
)
class WordpressImporterTestsYoastEnabled(TestCase):
    """
    We check here that if the Yoast plugin is enabled import the search description
    from there.
    If the search description is blank or not available then we import the
    <item><description>...</description></item> field.
    If the field is empty then search_description is set as a blank value.
    """

    fixtures = [
        f"{FIXTURES_PATH}/dump.json",
    ]

    def setUp(self):
        self.importer = WordpressImporter(f"{FIXTURES_PATH}/raw_xml.xml")
        self.logger = Logger(LOG_DIR)
        self.importer.run(
            logger=self.logger,
            app_for_pages=IMPORTER_RUN_PARAMS_TEST_OVERRIDE_1["app_for_pages"],
            model_for_pages=IMPORTER_RUN_PARAMS_TEST_OVERRIDE_1["model_for_pages"],
            parent_id=IMPORTER_RUN_PARAMS_TEST_OVERRIDE_1["parent_id"],
            page_types=IMPORTER_RUN_PARAMS_TEST_OVERRIDE_1["page_types"],
            page_statuses=IMPORTER_RUN_PARAMS_TEST_OVERRIDE_1["page_statuses"],
        )

        self.parent_page = Page.objects.get(
            id=IMPORTER_RUN_PARAMS_TEST_OVERRIDE_1["parent_id"]
        )
        self.imported_pages = self.parent_page.get_children().all()
        self.published_pages = self.parent_page.get_children().live()
        self.draft_pages = self.parent_page.get_children().filter(live=False)

    def test_page_field_values_with_yoast_plugin_enabled(self):
        self.assertEqual(
            self.published_pages.first().search_description,
            "a search description from yoast for Item one",
        )


IMPORTER_RUN_PARAMS_TEST_OVERRIDE_2 = {
    "app_for_pages": "wagtail_wordpress_import_test",
    "model_for_pages": "TestPage",
    "parent_id": "2",
    "page_types": ["testpostmeta"],
    "page_statuses": ["publish", "draft"],
}


@override_settings(WAGTAIL_WORDPRESS_IMPORT_YOAST_PLUGIN_ENABLED=True)
class WordpressImporterTestsYoastEnabledMissingTag(TestCase):
    """
    This tests when the expected config for Yoast is different from the
    package default which defaults to use the
    <item><description>...</description></item> field.
    """

    fixtures = [
        f"{FIXTURES_PATH}/dump.json",
    ]

    def setUp(self):
        self.importer = WordpressImporter(f"{FIXTURES_PATH}/raw_xml.xml")
        self.logger = Logger(LOG_DIR)
        self.importer.run(
            logger=self.logger,
            app_for_pages=IMPORTER_RUN_PARAMS_TEST_OVERRIDE_2["app_for_pages"],
            model_for_pages=IMPORTER_RUN_PARAMS_TEST_OVERRIDE_2["model_for_pages"],
            parent_id=IMPORTER_RUN_PARAMS_TEST_OVERRIDE_2["parent_id"],
            page_types=IMPORTER_RUN_PARAMS_TEST_OVERRIDE_2["page_types"],
            page_statuses=IMPORTER_RUN_PARAMS_TEST_OVERRIDE_2["page_statuses"],
        )

        self.parent_page = Page.objects.get(
            id=IMPORTER_RUN_PARAMS_TEST_OVERRIDE_2["parent_id"]
        )
        self.imported_pages = self.parent_page.get_children().all()
        self.published_pages = self.parent_page.get_children().live()
        self.draft_pages = self.parent_page.get_children().filter(live=False)

    def test_page_field_values_with_yoast_plugin_enabled(self):
        self.assertEqual(
            self.published_pages.first().search_description,
            "This page has a default description",
        )


IMPORTER_RUN_PARAMS_TEST_OVERRIDE_3 = {
    "app_for_pages": "wagtail_wordpress_import_test",
    "model_for_pages": "TestPage",
    "parent_id": "2",
    "page_types": ["postmetachanged"],
    "page_statuses": ["publish", "draft"],
}


@override_settings(
    WAGTAIL_WORDPRESS_IMPORT_YOAST_PLUGIN_ENABLED=True,
    WAGTAIL_WORDPRESS_IMPORT_YOAST_PLUGIN_MAPPING={
        "xml_item_key": "wp:postmeta",
        "description_key": "wp:meta_key",
        "description_value": "wp:meta_value",
        "description_key_value": "metadescription",
    },
)
class WordpressImporterTestsYoastEnabledChangedKey(TestCase):
    """
    This tests a different configuration for Yoast.
    The key for the search description is not the same as the package default.
    If the search description is blank or not available then we import the
    <item><description>...</description></item> field.
    If the field is empty then search_description is set as a blank value.
    """

    fixtures = [
        f"{FIXTURES_PATH}/dump.json",
    ]

    def setUp(self):
        self.importer = WordpressImporter(f"{FIXTURES_PATH}/raw_xml.xml")
        self.logger = Logger(LOG_DIR)
        self.importer.run(
            logger=self.logger,
            app_for_pages=IMPORTER_RUN_PARAMS_TEST_OVERRIDE_3["app_for_pages"],
            model_for_pages=IMPORTER_RUN_PARAMS_TEST_OVERRIDE_3["model_for_pages"],
            parent_id=IMPORTER_RUN_PARAMS_TEST_OVERRIDE_3["parent_id"],
            page_types=IMPORTER_RUN_PARAMS_TEST_OVERRIDE_3["page_types"],
            page_statuses=IMPORTER_RUN_PARAMS_TEST_OVERRIDE_3["page_statuses"],
        )

        self.parent_page = Page.objects.get(
            id=IMPORTER_RUN_PARAMS_TEST_OVERRIDE_3["parent_id"]
        )
        self.imported_pages = self.parent_page.get_children().all()
        self.published_pages = self.parent_page.get_children().live()
        self.draft_pages = self.parent_page.get_children().filter(live=False)

    def test_page_field_values_with_yoast_plugin_enabled(self):
        self.assertEqual(
            self.published_pages.first().search_description,
            "a search description from yoast using a different key",
        )
