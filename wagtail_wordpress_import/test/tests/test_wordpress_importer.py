import os
from io import StringIO
from xml.dom import pulldom

from django.test import TestCase, override_settings

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


IMPORTER_RUN_PARAMS_TEST_OVERRIDE_1 = {
    "app_for_pages": "example",
    "model_for_pages": "TestPage",
    "parent_id": "2",
    "page_types": ["post"],
    "page_statuses": ["publish", "draft"],
}


@override_settings(WAGTAIL_WORDPRESS_IMPORT_YOAST_PLUGIN_ENABLED=True)
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
    "app_for_pages": "example",
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
    "app_for_pages": "example",
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


@override_settings(
    WAGTAIL_WORDPRESS_IMPORT_YOAST_PLUGIN_ENABLED=True,
    WAGTAIL_WORDPRESS_IMPORT_YOAST_PLUGIN_MAPPING={
        "xml_item_key": "wp:postmeta",
        "description_key": "wp:meta_key",
        "description_value": "wp:meta_value",
        "description_key_value": "_yoast_wpseo_metadesc",
    },
)
class TestYoastMetaTags(TestCase):
    # @patch("wagtail_wordpress_import.importers.wordpress.pulldom")
    def setUp(self):
        self.logger = Logger("foo")

    def build_xml_stream(self, xml_fragment):
        """Formats the boilerplate XML template with the provided fragment."""

        return StringIO(
            """
            <rss xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/" xmlns:wp="http://wordpress.org/export/1.2/" version="2.0">
            <channel>
                <title>Foo</title>
                <link>https://www.example.com</link>
                <pubDate>Fri, 30 Jul 2021 11:56:01 +0000</pubDate>
                <language>en-US</language>
                <item>
                    <content:encoded />"""
            + xml_fragment
            + """
                </item>
            </channel>
            </rss>
            """
        )

    def process_item(self, xml_stream):
        """Turn an XML stream into a node dict

        We expect there to be only one node in the XML stream.

        This is duplicating a bunch of code from WorpressImporter. To make this a better
        unit test, we should instead make WordpressImporter more patchable, and less
        reliant on detecting app, Page IDs and logging configuration within its run
        method.
        """
        xml_doc = pulldom.parse(xml_stream)
        for event, node in xml_doc:
            if event == pulldom.START_ELEMENT and node.tagName == "item":
                xml_doc.expandNode(node)
                item = node_to_dict(node)
                wordpress_item = WordpressItem(item, self.logger)
        return wordpress_item

    def test_building_xml_stream(self):
        """This is just a test that our in-class fixture builder works okay.

        This unit test is a bit sensitive of blank lines and indentation, but the rest
        don't really matter so long as we format valid XML.
        """
        fragment = """
                    <description/>
                    <description>Another description</description>
                    <wp:postmeta>
                        <wp:meta_key>Radiators</wp:meta_key>
                        <wp:meta_value>Arguments</wp:meta_value>
                    </wp:postmeta>
                    <wp:postmeta>
                        <wp:meta_key>Jam</wp:meta_key>
                        <wp:meta_value>Haircuts</wp:meta_value>
                    </wp:postmeta>"""
        built = self.build_xml_stream(fragment).read()
        expected = StringIO(
            """
            <rss xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/" xmlns:wp="http://wordpress.org/export/1.2/" version="2.0">
            <channel>
                <title>Foo</title>
                <link>https://www.example.com</link>
                <pubDate>Fri, 30 Jul 2021 11:56:01 +0000</pubDate>
                <language>en-US</language>
                <item>
                    <content:encoded />
                    <description/>
                    <description>Another description</description>
                    <wp:postmeta>
                        <wp:meta_key>Radiators</wp:meta_key>
                        <wp:meta_value>Arguments</wp:meta_value>
                    </wp:postmeta>
                    <wp:postmeta>
                        <wp:meta_key>Jam</wp:meta_key>
                        <wp:meta_value>Haircuts</wp:meta_value>
                    </wp:postmeta>
                </item>
            </channel>
            </rss>
            """
        ).read()
        self.maxDiff = None
        self.assertEqual(built, expected)

    def test_parsing_with_one_matching_postmeta_tag(self):
        xml_stream = self.build_xml_stream(
            """
                <wp:postmeta>
                    <wp:meta_key>_yoast_wpseo_metadesc</wp:meta_key>
                    <wp:meta_value>this is the expected description</wp:meta_value>
                </wp:postmeta>
            """
        )
        wordpress_item = self.process_item(xml_stream)
        description = wordpress_item.get_yoast_description_value()
        self.assertEqual(description, "this is the expected description")

    def test_parsing_with_one_matching_postmeta_tag_among_multiple(self):
        xml_stream = self.build_xml_stream(
            """
                <wp:postmeta>
                    <wp:meta_key>_yoast_wpseo_metadesc</wp:meta_key>
                    <wp:meta_value>this is the expected description</wp:meta_value>
                </wp:postmeta>
                <wp:postmeta>
                    <wp:meta_key>ham</wp:meta_key>
                    <wp:meta_value>eggs</wp:meta_value>
                </wp:postmeta>
                <wp:postmeta>
                    <wp:meta_key>sausages</wp:meta_key>
                    <wp:meta_value>spam</wp:meta_value>
                </wp:postmeta>
            """
        )
        wordpress_item = self.process_item(xml_stream)
        description = wordpress_item.get_yoast_description_value()
        self.assertEqual(description, "this is the expected description")

    def test_parsing_with_one_unrelated_postmeta_tag(self):
        xml_stream = self.build_xml_stream(
            """
                <wp:postmeta>
                    <wp:meta_key>_thumbnail_id</wp:meta_key>
                    <wp:meta_value>43124</wp:meta_value>
                </wp:postmeta>
            """
        )
        wordpress_item = self.process_item(xml_stream)
        description = wordpress_item.get_yoast_description_value()
        # Expect an empty string, as the tag is not the one we're looking for
        self.assertEqual(description, "")

    def test_parsing_with_multiple_unrelated_postmeta_tags(self):
        xml_stream = self.build_xml_stream(
            """
                <wp:postmeta>
                    <wp:meta_key>ham</wp:meta_key>
                    <wp:meta_value>eggs</wp:meta_value>
                </wp:postmeta>
                <wp:postmeta>
                    <wp:meta_key>sausages</wp:meta_key>
                    <wp:meta_value>spam</wp:meta_value>
                </wp:postmeta>
            """
        )
        wordpress_item = self.process_item(xml_stream)
        description = wordpress_item.get_yoast_description_value()
        # Expect an empty string, as none of the tags is the one we're looking for
        self.assertEqual(description, "")

    def test_description_fallback_with_one_unrelated_postmeta_tag(self):
        xml_stream = self.build_xml_stream(
            """
                <description>Use this</description>
                <wp:postmeta>
                    <wp:meta_key>_thumbnail_id</wp:meta_key>
                    <wp:meta_value>43124</wp:meta_value>
                </wp:postmeta>
            """
        )
        wordpress_item = self.process_item(xml_stream)
        description = wordpress_item.get_yoast_description_value()
        self.assertEqual(description, "Use this")

    def test_description_fallback_with_multiple_unrelated_postmeta_tags(self):
        xml_stream = self.build_xml_stream(
            """
                <description>Use this</description>
                <wp:postmeta>
                    <wp:meta_key>ham</wp:meta_key>
                    <wp:meta_value>eggs</wp:meta_value>
                </wp:postmeta>
                <wp:postmeta>
                    <wp:meta_key>sausages</wp:meta_key>
                    <wp:meta_value>spam</wp:meta_value>
                </wp:postmeta>
            """
        )
        wordpress_item = self.process_item(xml_stream)
        description = wordpress_item.get_yoast_description_value()
        self.assertEqual(description, "Use this")

    def test_empty_description_fallback_with_one_unrelated_postmeta_tag(self):
        xml_stream = self.build_xml_stream(
            """
                <description />
                <wp:postmeta>
                    <wp:meta_key>_thumbnail_id</wp:meta_key>
                    <wp:meta_value>43124</wp:meta_value>
                </wp:postmeta>
            """
        )
        wordpress_item = self.process_item(xml_stream)
        description = wordpress_item.get_yoast_description_value()
        # Expect an empty string, as neither the tags nor description provided anything
        self.assertEqual(description, "")

    def test_empty_description_fallback_with_multiple_unrelated_postmeta_tags(self):
        xml_stream = self.build_xml_stream(
            """
                <description />
                <wp:postmeta>
                    <wp:meta_key>ham</wp:meta_key>
                    <wp:meta_value>eggs</wp:meta_value>
                </wp:postmeta>
                <wp:postmeta>
                    <wp:meta_key>sausages</wp:meta_key>
                    <wp:meta_value>spam</wp:meta_value>
                </wp:postmeta>
            """
        )
        wordpress_item = self.process_item(xml_stream)
        description = wordpress_item.get_yoast_description_value()
        # Expect an empty string, as none of the tags or description provided anything
        self.assertEqual(description, "")
