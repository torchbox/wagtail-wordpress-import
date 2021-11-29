import json
import os
from collections import Counter
from datetime import datetime
from xml.dom import pulldom

from django.test import TestCase, override_settings
from example.models import Category
from wagtail.core.models import Page
from wagtail_wordpress_import.functions import node_to_dict
from wagtail_wordpress_import.importers.wordpress import (
    WordpressImporter,
    WordpressItem,
)
from wagtail_wordpress_import.logger import Logger

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/fixtures"
LOG_DIR = "fakedir"
IMPORTER_RUN_PARAMS_TEST = {
    "app_for_pages": "example",
    "model_for_pages": "TestPage",
    "parent_id": "2",
    "page_types": ["post", "page"],
    "page_statuses": ["publish", "draft"],
}


class WordpressItemTests(TestCase):
    def setUp(self):
        self.logger = Logger("fakedir")
        body_html = """<p>Dummmy text</p><p>Dummmy text</p><p>Dummmy text</p>"""
        self.good_node = {
            "title": "Page Title",
            "wp:post_name": "page-title",
            "wp:post_date_gmt": "2017-03-12 17:53:57",
            "wp:post_modified_gmt": "2018-12-04 11:49:24",
            "content:encoded": body_html,
            "wp:post_id": "1000",
            "wp:post_type": "post",
            "link": "http://www.example.com",
        }
        self.bad_node = {
            "title": "Page Title",
            "wp:post_name": "",
            "wp:post_date_gmt": "0000-00-00 00:00:00",
            "wp:post_modified_gmt": "0000-00-00 00:00:00",
            "content:encoded": body_html,
            "wp:post_id": "1000",
            "wp:post_type": "post",
            "link": "",
        }

    def test_all_fields_with_good_data(self):
        wordpress_item = WordpressItem(self.good_node, self.logger)
        title = wordpress_item.cleaned_data["title"]
        slug = wordpress_item.cleaned_data["slug"]
        first_published_at = wordpress_item.cleaned_data["first_published_at"]
        last_published_at = wordpress_item.cleaned_data["last_published_at"]
        latest_revision_created_at = wordpress_item.cleaned_data[
            "latest_revision_created_at"
        ]
        body = wordpress_item.cleaned_data["body"]
        wp_post_id = wordpress_item.cleaned_data["wp_post_id"]
        wp_post_type = wordpress_item.cleaned_data["wp_post_type"]
        wp_link = wordpress_item.cleaned_data["wp_link"]
        wp_raw_content = wordpress_item.debug_content["filter_linebreaks_wp"]
        wp_processed_content = wordpress_item.debug_content[
            "filter_transform_inline_styles"
        ]
        wp_block_json = wordpress_item.debug_content["block_json"]

        self.assertEqual(title, "Page Title")
        self.assertEqual(slug, "page-title")
        self.assertIsInstance(first_published_at, datetime)
        self.assertIsInstance(last_published_at, datetime)
        self.assertIsInstance(latest_revision_created_at, datetime)
        self.assertIsInstance(json.dumps(body), str)
        self.assertEqual(wp_post_id, 1000)
        self.assertEqual(wp_post_type, "post")
        self.assertEqual(wp_link, "http://www.example.com")
        self.assertIsInstance(wp_raw_content, str)
        self.assertIsInstance(wp_processed_content, str)
        self.assertIsInstance(wp_block_json, list)
        self.assertTrue(
            len(wp_block_json), 1
        )  # we are only parsing consecutive paragraphs so the will only be one block (rich_text)

    def test_cleaned_fields(self):
        wordpress_item = WordpressItem(self.bad_node, self.logger)
        slug = wordpress_item.cleaned_data["slug"]
        first_published_at = wordpress_item.cleaned_data["first_published_at"]
        last_published_at = wordpress_item.cleaned_data["last_published_at"]
        latest_revision_created_at = wordpress_item.cleaned_data[
            "latest_revision_created_at"
        ]
        wp_link = wordpress_item.cleaned_data["wp_link"]
        self.assertEqual(slug, "page-title")
        self.assertIsInstance(first_published_at, datetime)
        self.assertIsInstance(last_published_at, datetime)
        self.assertIsInstance(latest_revision_created_at, datetime)
        self.assertEqual(wp_link, "")


@override_settings(
    BASE_URL="http://localhost:8000",
    WAGTAIL_WORDPRESS_IMPORT_CATEGORY_PLUGIN_ENABLED=True,
    WAGTAIL_WORDPRESS_IMPORT_CATEGORY_PLUGIN_MODEL="example.models.Category",
)  # testing requires a live domain for requests to use, this is something I need to change before package release
# mocking of somesort, using localhost:8000 for now
class WordpressItemImportTests(TestCase):
    from example.models import Category

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

    def test_category_snippets_are_saved(self):
        snippets = Category.objects.all()
        self.assertEqual(len(snippets), 4)

    def test_page_one_has_categories(self):
        page_one = self.imported_pages.get(title="Item one title")
        categories = page_one.specific.categories.all()
        self.assertEqual(2, categories.count())
        self.assertEqual(categories[0].name, "Blogging")
        self.assertEqual(categories[1].name, "Life")

    def test_page_two_has_categories(self):
        page_two = self.imported_pages.get(title="Item two title")
        categories = page_two.specific.categories.all()
        self.assertEqual(3, categories.count())
        self.assertEqual(categories[0].name, "Blogging")
        self.assertEqual(categories[1].name, "Cars")
        self.assertEqual(categories[2].name, "Computing")

    def test_short_category_is_not_imported(self):
        page_one = self.imported_pages.get(title="Item one title")
        categories = [category.name for category in page_one.specific.categories.all()]
        self.assertNotIn("A", categories)

    def test_categories_have_no_duplicate_entries(self):
        categories = [category.name for category in Category.objects.all()]
        duplicates = [
            k for k, v in Counter(categories).items() if v > 1
        ]  # duplicates will be empty if no duplicate category names exist
        self.assertEqual(len(duplicates), 0)


@override_settings(
    BASE_URL="http://localhost:8000",
    WAGTAIL_WORDPRESS_IMPORT_CATEGORY_PLUGIN_ENABLED=True,
    WAGTAIL_WORDPRESS_IMPORT_CATEGORY_PLUGIN_MODEL="example.models.Category",
)  # testing requires a live domain for requests to use, this is something I need to change before package release
# mocking of somesort, using localhost:8000 for now
class WordpressItemImportTestsNoCategories(TestCase):
    from example.models import Category

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
            page_types=["hasnocategories"],
            page_statuses=["hasnocategories"],
        )

        self.parent_page = Page.objects.get(id=IMPORTER_RUN_PARAMS_TEST["parent_id"])
        self.imported_pages = self.parent_page.get_children().all()

    def test_page_has_no_categories(self):
        page = self.imported_pages.first()
        categories = page.specific.categories.all()
        self.assertEqual(0, categories.count())

    def test_categories_count_is_zero(self):
        count = Category.objects.count()
        self.assertEqual(count, 0)


IMPORTER_RUN_PARAMS_TEST_OVERRIDE_1 = {
    "app_for_pages": "example",
    "model_for_pages": "TestPage",
    "parent_id": "2",
    "page_types": ["post"],
    "page_statuses": ["publish"],
}


@override_settings(
    WAGTAIL_WORDPRESS_IMPORT_YOAST_PLUGIN_ENABLED=True,
)
class WordpressImporterTestsYoastMetaDescriptions(TestCase):
    """
    This tests when a wp:postmeta for none single or multiple keys in the XML file.
    If the meta key for yoast is not present the <description></description> content is returned.
    """

    fixtures = [
        f"{FIXTURES_PATH}/dump.json",
    ]

    def setUp(self):
        self.logger = Logger("fakedir")
        xml_file = open(f"{FIXTURES_PATH}/post_meta.xml", "rb")
        xml_doc = pulldom.parse(xml_file)
        self.items_dict = []
        for event, node in xml_doc:
            if event == pulldom.START_ELEMENT and node.tagName == "item":
                xml_doc.expandNode(node)
                self.items_dict.append(node_to_dict(node))

    def test_items_dict_0(self):
        # self.items_dict[0] = the single item wp:post_meta without yoast
        wordpress_item = WordpressItem(self.items_dict[0], self.logger)
        self.assertEqual(
            wordpress_item.get_yoast_description_value(),
            "This page has a default description",
        )

    def test_items_dict_1(self):
        # self.items_dict[1] = the multiple item wp:post_meta
        wordpress_item = WordpressItem(self.items_dict[1], self.logger)
        self.assertEqual(
            wordpress_item.get_yoast_description_value(),
            "This page has a default description",
        )

    def test_items_dict_2(self):
        # self.items_dict[2] = the single item wp:post_meta with yoast
        wordpress_item = WordpressItem(self.items_dict[2], self.logger)
        self.assertEqual(
            wordpress_item.get_yoast_description_value(),
            "This is a yoast metadesc!",
        )

    def test_items_dict_3(self):
        # self.items_dict[3] = the multiple item wp:post_meta with yoast
        wordpress_item = WordpressItem(self.items_dict[3], self.logger)
        self.assertEqual(
            wordpress_item.get_yoast_description_value(),
            "This is a yoast metadesc!",
        )

    def test_items_dict_4(self):
        # self.items_dict[3] = the multiple item wp:post_meta with yoast
        wordpress_item = WordpressItem(self.items_dict[4], self.logger)
        self.assertEqual(
            wordpress_item.get_yoast_description_value(),
            "This page has a default description",
        )


class WordpressImporterTestsCleanWpPostMeta(TestCase):
    """
    This tests the post meta items retrieved from an XML file
    are extracted correctly in WordpressItem().clean_wp_post_meta()
    for various scenarios
    """

    fixtures = [
        f"{FIXTURES_PATH}/dump.json",
    ]

    def setUp(self):
        self.logger = Logger("fakedir")
        xml_file = open(f"{FIXTURES_PATH}/post_meta.xml", "rb")
        xml_doc = pulldom.parse(xml_file)
        self.items_dict = []
        for event, node in xml_doc:
            if event == pulldom.START_ELEMENT and node.tagName == "item":
                xml_doc.expandNode(node)
                self.items_dict.append(node_to_dict(node))

    def test_items_dict_0(self):
        # self.items_dict[0] = the single item wp:post_meta without yoast
        wordpress_item = WordpressItem(self.items_dict[0], self.logger)
        thumbnail_id = wordpress_item.clean_wp_post_meta()["thumbnail_id"]
        self.assertEqual(thumbnail_id, 43124)

    def test_items_dict_1(self):
        # self.items_dict[1] = the multiple item wp:post_meta
        wordpress_item = WordpressItem(self.items_dict[1], self.logger)
        post_meta = wordpress_item.clean_wp_post_meta()
        self.assertEqual(post_meta["facebook_shares"], 0)
        self.assertEqual(post_meta["pinterest_shares"], 0)
        self.assertEqual(post_meta["twitter_shares"], 0)

    def test_items_dict_2(self):
        # self.items_dict[2] = the single item wp:post_meta with yoast
        wordpress_item = WordpressItem(self.items_dict[2], self.logger)
        post_meta = wordpress_item.clean_wp_post_meta()
        self.assertEqual(post_meta["yoast_wpseo_metadesc"], "This is a yoast metadesc!")

    def test_items_dict_3(self):
        # self.items_dict[3] = the multiple item wp:post_meta with yoast
        wordpress_item = WordpressItem(self.items_dict[3], self.logger)
        post_meta = wordpress_item.clean_wp_post_meta()
        self.assertEqual(post_meta["facebook_shares"], 0)
        self.assertEqual(post_meta["pinterest_shares"], 0)
        self.assertEqual(post_meta["twitter_shares"], 0)
        self.assertEqual(post_meta["yoast_wpseo_metadesc"], "This is a yoast metadesc!")

    def test_items_dict_4(self):
        # self.items_dict[4] = has no wp:post_meta items
        wordpress_item = WordpressItem(self.items_dict[4], self.logger)
        with self.assertRaises(KeyError):
            post_meta = wordpress_item.clean_wp_post_meta()["wp:postmeta"]
