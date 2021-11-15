import os
from io import StringIO
from xml.dom import pulldom

from django.test import TestCase, override_settings
from wagtail.core.models import Page
from wagtail_wordpress_import.block_builder import conf_promote_child_tags
from wagtail_wordpress_import.functions import node_to_dict
from wagtail_wordpress_import.importers.import_hooks import (
    import_hooks_xml_items_to_cache,
)
from wagtail_wordpress_import.importers.wordpress import WordpressImporter
from wagtail_wordpress_import.logger import Logger

from wagtail_wordpress_import.xml_boilerplate import (
    build_xml_stream,
    generate_temporay_file,
)

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/fixtures"
LOG_DIR = "fakedir"


"""Tests for the Import Hooks Items Cache"""


class TestImportHooksOverrideItemTagConfig(TestCase):
    @override_settings(
        WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE={
            "foo": {"DATA_TAG": "datatagname", "FUNCTION": "path.to.function"},
            "bar": {"DATA_TAG": "datatagname", "FUNCTION": "path.to.function"},
        }
    )
    def test_persist_tags_config(self):
        self.assertEqual(
            import_hooks_xml_items_to_cache(),
            {
                "foo": {"DATA_TAG": "datatagname", "FUNCTION": "path.to.function"},
                "bar": {"DATA_TAG": "datatagname", "FUNCTION": "path.to.function"},
            },
        )


@override_settings(
    WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE={
        "foo": {"DATA_TAG": "datatagname", "FUNCTION": "path.to.function"},
        "bar": {"DATA_TAG": "datatagname", "FUNCTION": "path.to.function"},
    },
)
class TestImportHooksXmlItemPersisted(TestCase):
    def setUp(self):
        self.logger = Logger("foo")
        self.items_cache = None

    def process_item(self, xml_stream):
        """Turn an XML stream into a node dict
        We expect there to be only one node in the XML stream.
        This is duplicating a bunch of code from WorpressImporter. To make this a better
        unit test, we should instead make WordpressImporter more patchable, and less
        reliant on detecting app, Page IDs and logging configuration within its run
        method.
        """
        self.importer = WordpressImporter(xml_stream)
        xml_doc = pulldom.parse(xml_stream)
        for event, node in xml_doc:
            if event == pulldom.START_ELEMENT and node.tagName == "item":
                xml_doc.expandNode(node)
                item = node_to_dict(node)
                for hook in import_hooks_xml_items_to_cache():
                    if item.get("wp:post_type") == hook:
                        self.items_cache = self.importer.cache_item_tags(item, hook)

        return self.items_cache

    def test_xml_items_are_cached_without_duplicates(self):
        # the fragment is not a complete XML item, but it is enough to test
        # the second item with title foo-item should not be cached as it's a
        # duplicate of the first item
        fragment = """
        <item>
            <title>foo-item</title>
            <link>https://www.example.com/foo-item/</link>
            <pubDate>Tue, 13 Jul 2010 16:16:46 +0000</pubDate>
            <guid isPermaLink="false">https://www.example.com/foo.jpg</guid>
            <wp:post_id>100</wp:post_id>
            <wp:post_date>2010-07-13 12:16:46</wp:post_date>
            <wp:post_date_gmt>2010-07-13 16:16:46</wp:post_date_gmt>
            <wp:post_modified>2010-07-13 12:16:46</wp:post_modified>
            <wp:post_modified_gmt>2010-07-13 16:16:46</wp:post_modified_gmt>
            <wp:post_name>foo-item</wp:post_name>
            <wp:post_type>foo</wp:post_type>
        </item>
        <item>
            <title>foo-item</title>
            <link>https://www.example.com/foo-item/</link>
            <pubDate>Tue, 13 Jul 2010 16:16:46 +0000</pubDate>
            <guid isPermaLink="false">https://www.example.com/foo.jpg</guid>
            <wp:post_id>100</wp:post_id>
            <wp:post_date>2010-07-13 12:16:46</wp:post_date>
            <wp:post_date_gmt>2010-07-13 16:16:46</wp:post_date_gmt>
            <wp:post_modified>2010-07-13 12:16:46</wp:post_modified>
            <wp:post_modified_gmt>2010-07-13 16:16:46</wp:post_modified_gmt>
            <wp:post_name>foo-item</wp:post_name>
            <wp:post_type>foo</wp:post_type>
        </item>
        <item>
            <title>bar-item</title>
            <link>https://www.example.com/bar-item/</link>
            <pubDate>Tue, 13 Jul 2010 16:16:46 +0000</pubDate>
            <guid isPermaLink="false">https://www.example.com/bar.jpg</guid>
            <wp:post_id>200</wp:post_id>
            <wp:post_date>2010-07-13 12:16:46</wp:post_date>
            <wp:post_date_gmt>2010-07-13 16:16:46</wp:post_date_gmt>
            <wp:post_modified>2010-07-13 12:16:46</wp:post_modified>
            <wp:post_modified_gmt>2010-07-13 16:16:46</wp:post_modified_gmt>
            <wp:post_name>bar-item</wp:post_name>
            <wp:post_type>bar</wp:post_type>
        </item>
        """
        built = build_xml_stream(xml_items_fragment=fragment).read()
        cache = self.process_item(StringIO(built))

        self.assertIsInstance(cache.foo, list)
        self.assertEqual(len(cache.foo), 1)

        # values of the first item in the foo attribute
        foo = cache.foo[0]
        self.assertEqual(foo["title"], "foo-item")
        self.assertEqual(foo["link"], "https://www.example.com/foo-item/")
        self.assertEqual(foo["pubDate"], "Tue, 13 Jul 2010 16:16:46 +0000")
        self.assertEqual(foo["guid"], "https://www.example.com/foo.jpg")
        self.assertEqual(foo["wp:post_id"], 100)
        self.assertEqual(foo["wp:post_date"], "2010-07-13 12:16:46")
        self.assertEqual(foo["wp:post_date_gmt"], "2010-07-13 16:16:46")
        self.assertEqual(foo["wp:post_modified"], "2010-07-13 12:16:46")
        self.assertEqual(foo["wp:post_modified_gmt"], "2010-07-13 16:16:46")
        self.assertEqual(foo["wp:post_name"], "foo-item")
        self.assertEqual(foo["wp:post_type"], "foo")

        self.assertIsInstance(cache.bar, list)
        self.assertEqual(len(cache.bar), 1)

        # values of the first item in the bar attribute
        foo = cache.bar[0]
        self.assertEqual(foo["title"], "bar-item")
        self.assertEqual(foo["link"], "https://www.example.com/bar-item/")
        self.assertEqual(foo["pubDate"], "Tue, 13 Jul 2010 16:16:46 +0000")
        self.assertEqual(foo["guid"], "https://www.example.com/bar.jpg")
        self.assertEqual(foo["wp:post_id"], 200)
        self.assertEqual(foo["wp:post_date"], "2010-07-13 12:16:46")
        self.assertEqual(foo["wp:post_date_gmt"], "2010-07-13 16:16:46")
        self.assertEqual(foo["wp:post_modified"], "2010-07-13 12:16:46")
        self.assertEqual(foo["wp:post_modified_gmt"], "2010-07-13 16:16:46")
        self.assertEqual(foo["wp:post_name"], "bar-item")
        self.assertEqual(foo["wp:post_type"], "bar")


class WordpressImporterTestsCheckXmlItemsNotCached(TestCase):
    """
    This tests that the XML tags are not cached during an import because there
    is no settings.WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE
    """

    fixtures = [
        f"{FIXTURES_PATH}/dump.json",
    ]

    def process_import(self, xml_stream):
        self.importer = WordpressImporter(xml_stream)
        self.logger = Logger(LOG_DIR)
        self.importer.run(
            logger=self.logger,
            app_for_pages="example",
            model_for_pages="TestPage",
            parent_id=2,
            page_types=["post"],
            page_statuses=["publish"],
        )
        self.parent_page = Page.objects.get(id=2)
        self.imported_pages = self.parent_page.get_children().all()

    def test_xml_items_not_cached(self):
        fragment = """
        <item>
            <title>foo-item</title>
            <link>https://www.example.com/foo-item/</link>
            <pubDate>Tue, 13 Jul 2010 16:16:46 +0000</pubDate>
            <guid isPermaLink="false">https://www.example.com/foo.jpg</guid>
            <wp:post_id>100</wp:post_id>
            <wp:post_date>2010-07-13 12:16:46</wp:post_date>
            <wp:post_date_gmt>2010-07-13 16:16:46</wp:post_date_gmt>
            <wp:post_modified>2010-07-13 12:16:46</wp:post_modified>
            <wp:post_modified_gmt>2010-07-13 16:16:46</wp:post_modified_gmt>
            <wp:post_name>foo-item</wp:post_name>
            <wp:post_type>foo</wp:post_type>
        </item>
        <item>
            <title>bar-item</title>
            <link>https://www.example.com/bar-item/</link>
            <pubDate>Tue, 13 Jul 2010 16:16:46 +0000</pubDate>
            <guid isPermaLink="false">https://www.example.com/bar.jpg</guid>
            <wp:post_id>200</wp:post_id>
            <wp:post_date>2010-07-13 12:16:46</wp:post_date>
            <wp:post_date_gmt>2010-07-13 16:16:46</wp:post_date_gmt>
            <wp:post_modified>2010-07-13 12:16:46</wp:post_modified>
            <wp:post_modified_gmt>2010-07-13 16:16:46</wp:post_modified_gmt>
            <wp:post_name>bar-item</wp:post_name>
            <wp:post_type>bar</wp:post_type>
        </item>
        <item>
            <title>A title</title>
            <link>https://www.example.com/a-title</link>
            <description />
            <content:encoded />
            <excerpt:encoded />
            <wp:post_id>44221</wp:post_id>
            <wp:post_date>2015-05-21 15:00:31</wp:post_date>
            <wp:post_date_gmt>2015-05-21 19:00:31</wp:post_date_gmt>
            <wp:post_modified>2015-05-21 15:00:44</wp:post_modified>
            <wp:post_modified_gmt>2015-05-21 19:00:44</wp:post_modified_gmt>
            <wp:comment_status>open</wp:comment_status>
            <wp:ping_status>closed</wp:ping_status>
            <wp:post_name>a-title</wp:post_name>
            <wp:status>publish</wp:status>
            <wp:post_type>post</wp:post_type>
        </item>
        """
        built_file = generate_temporay_file(
            build_xml_stream(xml_items_fragment=fragment).read()
        )

        self.process_import(built_file)

        # there should be one page imported
        self.assertEqual(self.imported_pages.count(), 1)
        self.assertEqual(self.imported_pages.first().title, "A title")

        # assertions for the content of items_cache, should be none
        self.assertEqual(len(self.importer.items_cache.__dict__.keys()), 0)


@override_settings(
    WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE={
        "foo": {"DATA_TAG": "datatagname", "FUNCTION": "path.to.function"},
        "bar": {"DATA_TAG": "datatagname", "FUNCTION": "path.to.function"},
    },
)
class WordpressImporterTestsCheckXmlItemsCached(TestCase):
    """
    This tests that the XML tags are cached during an import because
    settings.WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE is set
    """

    fixtures = [
        f"{FIXTURES_PATH}/dump.json",
    ]

    def process_import(self, xml_stream):
        self.importer = WordpressImporter(xml_stream)
        self.logger = Logger(LOG_DIR)
        self.importer.run(
            logger=self.logger,
            app_for_pages="example",
            model_for_pages="TestPage",
            parent_id=2,
            page_types=["post"],
            page_statuses=["publish"],
        )
        self.parent_page = Page.objects.get(id=2)
        self.imported_pages = self.parent_page.get_children().all()

    def test_xml_tags_not_cached(self):
        fragment = """
        <item>
            <title>foo-item</title>
            <link>https://www.example.com/foo-item/</link>
            <pubDate>Tue, 13 Jul 2010 16:16:46 +0000</pubDate>
            <guid isPermaLink="false">https://www.example.com/foo.jpg</guid>
            <wp:post_id>100</wp:post_id>
            <wp:post_date>2010-07-13 12:16:46</wp:post_date>
            <wp:post_date_gmt>2010-07-13 16:16:46</wp:post_date_gmt>
            <wp:post_modified>2010-07-13 12:16:46</wp:post_modified>
            <wp:post_modified_gmt>2010-07-13 16:16:46</wp:post_modified_gmt>
            <wp:post_name>foo-item</wp:post_name>
            <wp:post_type>foo</wp:post_type>
        </item>
        <item>
            <title>bar-item</title>
            <link>https://www.example.com/bar-item/</link>
            <pubDate>Tue, 13 Jul 2010 16:16:46 +0000</pubDate>
            <guid isPermaLink="false">https://www.example.com/bar.jpg</guid>
            <wp:post_id>200</wp:post_id>
            <wp:post_date>2010-07-13 12:16:46</wp:post_date>
            <wp:post_date_gmt>2010-07-13 16:16:46</wp:post_date_gmt>
            <wp:post_modified>2010-07-13 12:16:46</wp:post_modified>
            <wp:post_modified_gmt>2010-07-13 16:16:46</wp:post_modified_gmt>
            <wp:post_name>bar-item</wp:post_name>
            <wp:post_type>bar</wp:post_type>
        </item>
        <item>
            <title>A title</title>
            <link>https://www.example.com/a-title</link>
            <description />
            <content:encoded />
            <excerpt:encoded />
            <wp:post_id>44221</wp:post_id>
            <wp:post_date>2015-05-21 15:00:31</wp:post_date>
            <wp:post_date_gmt>2015-05-21 19:00:31</wp:post_date_gmt>
            <wp:post_modified>2015-05-21 15:00:44</wp:post_modified>
            <wp:post_modified_gmt>2015-05-21 19:00:44</wp:post_modified_gmt>
            <wp:comment_status>open</wp:comment_status>
            <wp:ping_status>closed</wp:ping_status>
            <wp:post_name>a-title</wp:post_name>
            <wp:status>publish</wp:status>
            <wp:post_type>post</wp:post_type>
        </item>
        """
        built_file = generate_temporay_file(
            build_xml_stream(xml_items_fragment=fragment).read()
        )

        self.process_import(built_file)

        # there should be one page imported
        self.assertEqual(self.imported_pages.count(), 1)
        self.assertEqual(self.imported_pages.first().title, "A title")

        self.assertEqual(len(self.importer.items_cache.__dict__.keys()), 2)
