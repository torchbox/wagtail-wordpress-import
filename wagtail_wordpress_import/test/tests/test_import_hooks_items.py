import os
from io import StringIO
from unittest import mock
from xml.dom import pulldom

from django.conf import settings
from django.test import TestCase, override_settings
from wagtail import VERSION as WAGTAIL_VERSION

if WAGTAIL_VERSION >= (3, 0):
    from wagtail.models import Page
else:
    from wagtail.core.models import Page

from wagtail_wordpress_import.functions import node_to_dict
from wagtail_wordpress_import.importers.wordpress import WordpressImporter
from wagtail_wordpress_import.logger import Logger
from wagtail_wordpress_import.test.tests.xml_boilerplate import (
    build_xml_stream,
    generate_temporay_file,
)

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/fixtures"
LOG_DIR = "fakedir"


class TestImportHooksOverrideItemTagConfig(TestCase):
    """The overridden conf should be return by import_hooks_xml_items_to_cache"""

    @override_settings(
        WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE={
            "foo": {"DATA_TAG": "datatagname", "FUNCTION": "path.to.function"},
            "bar": {"DATA_TAG": "datatagname", "FUNCTION": "path.to.function"},
        }
    )
    def test_persist_tags_config(self):
        self.assertEqual(
            getattr(settings, "WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE", {}),
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
    """The overridden config should result in ItemsCache instance contaiing two
    dicts with keys foo and bar. Each dict should contain all xml tags and
    values from the fragment"""

    def setUp(self):
        self.logger = Logger("foo")

    def process_item(self, xml_stream):
        """Turn an XML stream into a node dict
        This is duplicating a bunch of code from WordPressImporter. To test the ItemsCache
        instance on WordPressImporter.
        """
        self.importer = WordpressImporter(xml_stream)
        xml_doc = pulldom.parse(xml_stream)
        for event, node in xml_doc:
            if event == pulldom.START_ELEMENT and node.tagName == "item":
                xml_doc.expandNode(node)
                item = node_to_dict(node)
                post_type = item.get("wp:post_type")
                if post_type in getattr(
                    settings, "WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE", {}
                ):
                    self.importer.items_cache.add_item_to_cache(post_type, item)

        return self.importer.items_cache

    def test_xml_items_are_cached_without_duplicates(self):
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

        # Duplicates should be skipped.
        # In the fragment we have identical items with title foo-item
        self.assertEqual(len(cache.foo), 1)

        # Values of the first item in the ItemsCache instance foo attribute
        foo = cache.foo[0]

        # there should be no wp:postmeta in the cache
        with self.assertRaises(KeyError):
            foo["wp:postmeta"]

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

        # Values of the first item in the ItemsCache instance bar attribute
        bar = cache.bar[0]

        # there should be no wp:postmeta in the cache
        with self.assertRaises(KeyError):
            bar["wp:postmeta"]

        self.assertEqual(bar["title"], "bar-item")
        self.assertEqual(bar["link"], "https://www.example.com/bar-item/")
        self.assertEqual(bar["pubDate"], "Tue, 13 Jul 2010 16:16:46 +0000")
        self.assertEqual(bar["guid"], "https://www.example.com/bar.jpg")
        self.assertEqual(bar["wp:post_id"], 200)
        self.assertEqual(bar["wp:post_date"], "2010-07-13 12:16:46")
        self.assertEqual(bar["wp:post_date_gmt"], "2010-07-13 16:16:46")
        self.assertEqual(bar["wp:post_modified"], "2010-07-13 12:16:46")
        self.assertEqual(bar["wp:post_modified_gmt"], "2010-07-13 16:16:46")
        self.assertEqual(bar["wp:post_name"], "bar-item")
        self.assertEqual(bar["wp:post_type"], "bar")


class WordpressImporterTestsCheckXmlItemsNotCached(TestCase):
    """
    This tests that the XML tags are not cached during an import as there
    is no settings.WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE
    The item with <wp:post_type>post</wp:post_type> should be saved as a page
    """

    fixtures = [
        f"{FIXTURES_PATH}/dump.json",
    ]

    def process_import(self, xml_stream):
        self.importer = WordpressImporter(xml_stream)
        self.logger = Logger(LOG_DIR)
        self.importer.run(
            logger=self.logger,
            app_for_pages="wagtail_wordpress_import_test",
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

        # One page should be imported
        self.assertEqual(self.imported_pages.count(), 1)
        self.assertEqual(self.imported_pages.first().title, "A title")

        # ItemsCache instance should have no writable attributes
        self.assertEqual(len(self.importer.items_cache.__dict__.keys()), 0)


process_foo = mock.Mock()
process_bar = mock.Mock()


@override_settings(
    WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE={
        "foo": {
            "DATA_TAG": "datatagname",
            "FUNCTION": "wagtail_wordpress_import.test.tests.test_import_hooks_items.process_foo",
        },
        "bar": {
            "DATA_TAG": "datatagname",
            "FUNCTION": "wagtail_wordpress_import.test.tests.test_import_hooks_items.process_bar",
        },
    },
)
class WordpressImporterTestsCheckXmlItemsCached(TestCase):
    """
    This tests that the XML tags are cached during an import because
    settings.WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE is set.
    The process run here is WordpressImporter.run()
    """

    fixtures = [
        f"{FIXTURES_PATH}/dump.json",
    ]

    def process_import(self, xml_stream):
        self.importer = WordpressImporter(xml_stream)
        self.logger = Logger(LOG_DIR)
        self.importer.run(
            logger=self.logger,
            app_for_pages="wagtail_wordpress_import_test",
            model_for_pages="TestPage",
            parent_id=2,
            page_types=["post"],
            page_statuses=["publish"],
        )

    def test_xml_items_cached(self):
        """There is a place in WordPressImporter thats runs add_item_to_cache()
        that will populate the ItemsCache instance attributes"""
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

        # One page should be imported
        self.assertEqual(self.importer.imported_pages.count(), 1)
        self.assertEqual(self.importer.imported_pages.first().title, "A title")

        # ItemsCache instance should have 2 writable attributes
        self.assertEqual(len(self.importer.items_cache.__dict__.keys()), 2)

        process_foo.assert_called_once_with(
            self.importer.imported_pages,
            "datatagname",
            getattr(self.importer.items_cache, "foo"),
        )

        process_bar.assert_called_once_with(
            self.importer.imported_pages,
            "datatagname",
            getattr(self.importer.items_cache, "bar"),
        )
