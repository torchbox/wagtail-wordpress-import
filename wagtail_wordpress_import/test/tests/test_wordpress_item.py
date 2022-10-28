import json
import os
import re
from collections import Counter
from datetime import datetime
from xml.dom import pulldom

from django.test import TestCase, override_settings

try:
    from wagtail.models import Page
except ImportError:
    from wagtail.core.models import Page

from wagtail_wordpress_import.functions import node_to_dict
from wagtail_wordpress_import.importers.wordpress import (
    DEFAULT_PREFILTERS,
    WordpressImporter,
    WordpressItem,
)
from wagtail_wordpress_import.logger import Logger
from wagtail_wordpress_import.test.models import Category

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
        self.no_title = {
            "wp:post_name": "no-title",
            "wp:post_date_gmt": "2017-03-12 17:53:57",
            "wp:post_modified_gmt": "2018-12-04 11:49:24",
            "content:encoded": body_html,
            "wp:post_id": "1000",
            "wp:post_type": "post",
            "link": "http://www.example.com",
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

    def test_no_title_faked(self):
        wordpress_item = WordpressItem(self.no_title, self.logger)
        title = wordpress_item.cleaned_data["title"]

        self.assertEqual(
            self.no_title["wp:post_id"], "1000"
        )  # just a fixture regression test
        self.assertEqual(title, "no-title-available-1000")


@override_settings(
    WAGTAIL_WORDPRESS_IMPORTER_SOURCE_DOMAIN="http://localhost:8000",
    WAGTAIL_WORDPRESS_IMPORT_CATEGORY_PLUGIN_ENABLED=True,
    WAGTAIL_WORDPRESS_IMPORT_CATEGORY_PLUGIN_MODEL="wagtail_wordpress_import.test.models.Category",
)  # testing requires a live domain for requests to use, this is something I need to change before package release
# mocking of somesort, using localhost:8000 for now
class WordpressItemImportTests(TestCase):
    # from wagtail_wordpress_import.test.models import Category

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
        self.assertEqual(len(snippets), 5)

    def test_page_one_has_categories(self):
        page_one = self.imported_pages.get(title="Item one title")
        categories = page_one.specific.categories.all()
        self.assertEqual(3, categories.count())
        self.assertEqual(categories[0].name, "Blogging")
        self.assertEqual(categories[1].name, "Life")
        self.assertEqual(categories[2].name, "2016")

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
    WAGTAIL_WORDPRESS_IMPORTER_SOURCE_DOMAIN="http://localhost:8000",
    WAGTAIL_WORDPRESS_IMPORT_CATEGORY_PLUGIN_ENABLED=True,
    WAGTAIL_WORDPRESS_IMPORT_CATEGORY_PLUGIN_MODEL="wagtail_wordpress_import.test.models.Category",
)  # testing requires a live domain for requests to use, this is something I need to change before package release
# mocking of somesort, using localhost:8000 for now
class WordpressItemImportTestsNoCategories(TestCase):
    # from wagtail_wordpress_import.test.models import Category

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
    "app_for_pages": "wagtail_wordpress_import.test",
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
    This tests the wp_post_meta field contents after cleaning in
    WordpressItem().clean_wp_post_meta()
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
        self.assertEqual(post_meta["facebook_shares"], 100)
        self.assertEqual(post_meta["pinterest_shares"], 200)
        self.assertEqual(post_meta["twitter_shares"], 300)

    def test_items_dict_2(self):
        # self.items_dict[2] = the single item wp:post_meta with yoast
        wordpress_item = WordpressItem(self.items_dict[2], self.logger)
        post_meta = wordpress_item.clean_wp_post_meta()
        self.assertEqual(post_meta["yoast_wpseo_metadesc"], "This is a yoast metadesc!")

    def test_items_dict_3(self):
        # self.items_dict[3] = the multiple item wp:post_meta with yoast
        wordpress_item = WordpressItem(self.items_dict[3], self.logger)
        post_meta = wordpress_item.clean_wp_post_meta()
        self.assertEqual(post_meta["facebook_shares"], 10)
        self.assertEqual(post_meta["pinterest_shares"], 20)
        self.assertEqual(post_meta["twitter_shares"], 30)
        self.assertEqual(post_meta["yoast_wpseo_metadesc"], "This is a yoast metadesc!")

    def test_items_dict_4(self):
        # self.items_dict[4] = has no wp:post_meta items
        wordpress_item = WordpressItem(self.items_dict[4], self.logger)
        with self.assertRaises(KeyError):
            wordpress_item.clean_wp_post_meta()["wp:postmeta"]

    def test_items_dict_1_excluded_keys(self):
        wordpress_item = WordpressItem(self.items_dict[1], self.logger)
        cleaned_postmeta = wordpress_item.clean_wp_post_meta()
        with self.assertRaises(KeyError):
            cleaned_postmeta["wp:postmeta"]
        with self.assertRaises(KeyError):
            cleaned_postmeta["wp_post_meta"]
        with self.assertRaises(KeyError):
            cleaned_postmeta["content:encoded"]
        with self.assertRaises(KeyError):
            cleaned_postmeta["dc:creator"]
        with self.assertRaises(KeyError):
            cleaned_postmeta["wp:post_id"]

    def test_items_dict_1_included_keys(self):
        wordpress_item = WordpressItem(self.items_dict[1], self.logger)
        cleaned_postmeta = wordpress_item.clean_wp_post_meta()
        self.assertTrue("title" in cleaned_postmeta)
        self.assertTrue("dc_creator" in cleaned_postmeta)
        self.assertTrue("guid" in cleaned_postmeta)
        self.assertTrue("description" in cleaned_postmeta)
        self.assertTrue("wp_post_id" in cleaned_postmeta)
        self.assertTrue("wp_post_date" in cleaned_postmeta)
        self.assertTrue("category" in cleaned_postmeta)
        self.assertTrue("facebook_shares" in cleaned_postmeta)
        self.assertTrue("pinterest_shares" in cleaned_postmeta)
        self.assertTrue("twitter_shares" in cleaned_postmeta)


class TestWordpressItemPrefilterConfig(TestCase):
    def test_prefilter_content_default(self):
        # The expected output should be transformed after passing through the
        # the default prefilters
        node = {"content:encoded": "foo bar baz"}
        wordpress_item = WordpressItem(node, "")
        output = wordpress_item.prefilter_content(wordpress_item.raw_body)
        self.assertEqual(output, "<p>foo bar baz</p>\n")


class TestWordpressPrefilterDefaults(TestCase):
    def test_default_prefilters(self):
        self.assertIsInstance(DEFAULT_PREFILTERS, list)
        self.assertTrue(len(DEFAULT_PREFILTERS), 4)
        self.assertEqual(
            DEFAULT_PREFILTERS[0]["FUNCTION"],
            "wagtail_wordpress_import.prefilters.linebreaks_wp",
        )
        self.assertEqual(
            DEFAULT_PREFILTERS[1]["FUNCTION"],
            "wagtail_wordpress_import.prefilters.transform_shortcodes",
        )
        self.assertEqual(
            DEFAULT_PREFILTERS[2]["FUNCTION"],
            "wagtail_wordpress_import.prefilters.transform_inline_styles",
        )
        self.assertEqual(
            DEFAULT_PREFILTERS[3]["FUNCTION"],
            "wagtail_wordpress_import.prefilters.bleach_clean",
        )


def foo_filter(content, options):
    return content, options


def transform_foo(soup, tag):
    new_tag = soup.new_tag("foo")
    new_tag.string = tag.string
    tag.replace_with(new_tag)


class TestWordpressItemPrefilterOverride(TestCase):
    """Test developers' ability to edit settings.WAGTAIL_WORDPRESS_IMPORT_PREFILTERS"""

    @override_settings(WAGTAIL_WORDPRESS_IMPORT_PREFILTERS=[])
    def test_prefilter_content_no_filters(self):
        """Remove all pre-filters

        The expected output is the same as the input because there are no prefilters to
        apply to the content
        """
        node = {"content:encoded": "foo bar baz"}
        wordpress_item = WordpressItem(node, "")
        output = wordpress_item.prefilter_content(wordpress_item.raw_body)
        self.assertEqual(output, "foo bar baz")

    @override_settings(
        WAGTAIL_WORDPRESS_IMPORT_PREFILTERS=[
            {
                "FUNCTION": "wagtail_wordpress_import.test.tests.test_wordpress_item.foo_filter"
            }
        ]
    )
    def test_custom_provided_prefilter(self):
        """Provide a custom pre-filter

        The expected output is the same as the input because the applied filters do
        nothing and return the same value.
        """
        node = {"content:encoded": "foo bar baz"}
        wordpress_item = WordpressItem(node, "")
        output = wordpress_item.prefilter_content(wordpress_item.raw_body)
        self.assertEqual(output[0], "foo bar baz")
        self.assertEqual(output[1], None)

    @override_settings(
        WAGTAIL_WORDPRESS_IMPORT_PREFILTERS=[
            {
                "FUNCTION": "wagtail_wordpress_import.test.tests.test_wordpress_item.foo_filter",
                "OPTIONS": {"foo": "bar"},
            }
        ]
    )
    def test_custom_provided_prefilter_with_options(self):
        """Provide a custom pre-filter with options

        The expected output is the same as the input because the applied filters do
        nothing and return the same value.
        """
        node = {"content:encoded": "foo bar baz"}
        wordpress_item = WordpressItem(node, "")
        output = wordpress_item.prefilter_content(wordpress_item.raw_body)
        self.assertEqual(output[0], "foo bar baz")
        self.assertEqual(output[1], {"foo": "bar"})

    @override_settings(
        WAGTAIL_WORDPRESS_IMPORT_PREFILTERS=[
            {
                "FUNCTION": "wagtail_wordpress_import.prefilters.transform_inline_styles",
                "OPTIONS": {
                    "TRANSFORM_STYLES_MAPPING": [
                        (
                            re.compile(r"font-weight:bold", re.IGNORECASE),
                            "wagtail_wordpress_import.test.tests.test_wordpress_item.transform_foo",
                        )
                    ],
                },
            },
        ]
    )
    def test_transform_styles_filter_add_options(self):
        """Test that a developer can pass custom OPTIONS to transform_inline_styles.

        Here WAGTAIL_WORDPRESS_IMPORT_PREFILTERS contains only config for
        transform_inline_styles, so that other prefilters are not run, and it's easier
        to test the output.
        """
        node = {"content:encoded": '<p style="font-weight: bold">foo bar baz</p>'}
        wordpress_item = WordpressItem(node, "")
        output = wordpress_item.prefilter_content(wordpress_item.raw_body)
        self.assertEqual(output.strip(), "<foo>foo bar baz</foo>")
