import os
from io import StringIO
from xml.dom import pulldom

from django.conf import settings
from django.test import TestCase, override_settings

try:
    from wagtail.models import Page
except ImportError:
    from wagtail.core.models import Page

from wagtail_wordpress_import.functions import node_to_dict
from wagtail_wordpress_import.importers.wordpress import WordpressImporter
from wagtail_wordpress_import.logger import Logger
from wagtail_wordpress_import.xml_boilerplate import (
    build_xml_stream,
    generate_temporary_file,
)

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/fixtures"
LOG_DIR = "fakedir"


class TestImportHooksOverrideXmlTagConfig(TestCase):
    """The overridden conf should be return by import_hooks_xml_tags_to_cache"""

    @override_settings(
        WORDPRESS_IMPORT_HOOKS_TAGS_TO_CACHE={
            "wp:foo": {"DATA_TAG": "a:tag", "FUNCTION": "path.to.function"},
            "wp:bar": {"DATA_TAG": "a:tag", "FUNCTION": "path.to.function"},
        }
    )
    def test_persist_tags_config(self):
        self.assertEqual(
            getattr(settings, "WORDPRESS_IMPORT_HOOKS_TAGS_TO_CACHE", {}),
            {
                "wp:foo": {"DATA_TAG": "a:tag", "FUNCTION": "path.to.function"},
                "wp:bar": {"DATA_TAG": "a:tag", "FUNCTION": "path.to.function"},
            },
        )


@override_settings(
    WORDPRESS_IMPORT_HOOKS_TAGS_TO_CACHE={
        "wp:foo": {"DATA_TAG": "not:required", "FUNCTION": "path.to.function"},
        "wp:bar": {"DATA_TAG": "not:required", "FUNCTION": "path.to.function"},
    }
)
class TestImportHooksXmlTagsPersisted(TestCase):
    """The overridden config should result in TagsCache instance containing two
    dicts with keys foo and bar. Each dict should contain all XML tags and
    values from the fragment"""

    def setUp(self):
        self.logger = Logger("foo")

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
            if event == pulldom.START_ELEMENT and node.tagName in getattr(
                settings, "WORDPRESS_IMPORT_HOOKS_TAGS_TO_CACHE", {}
            ):
                xml_doc.expandNode(node)
                item = node_to_dict(node)
                self.importer.tags_cache.add_item_to_cache(node.tagName, item)

        return self.importer.tags_cache

    def test_xml_tags_are_cached_without_duplicates(self):
        fragment = """
        <wp:foo>
            <wp:foo_id>3</wp:foo_id>
            <wp:foo_login>rickw</wp:foo_login>
            <wp:foo_email>rick@example.com</wp:foo_email>
            <wp:foo_display_name>Rick Wakeman</wp:foo_display_name>
            <wp:foo_first_name>Rick</wp:foo_first_name>
            <wp:foo_last_name>Wakeman</wp:foo_last_name>
        </wp:foo>
        <wp:bar>
            <wp:bar_id>12345</wp:bar_id>
            <wp:bar_nicename>some-stuff</wp:bar_nicename>
        </wp:bar>
        <wp:bar>
            <wp:bar_id>12345</wp:bar_id>
            <wp:bar_nicename>some-stuff</wp:bar_nicename>
        </wp:bar>
        """
        built = build_xml_stream(xml_tags_fragment=fragment).read()
        cache = self.process_item(StringIO(built))

        # using getattr here because then keys can contain special characters
        foo = getattr(cache, "wp:foo")
        self.assertIsInstance(foo, list)
        self.assertEqual(len(foo), 1)
        self.assertIsInstance(foo[0], dict)

        # tests for first item in the list
        self.assertEqual(foo[0]["wp:foo_id"], 3)
        self.assertEqual(foo[0]["wp:foo_login"], "rickw")
        self.assertEqual(foo[0]["wp:foo_email"], "rick@example.com")
        self.assertEqual(foo[0]["wp:foo_display_name"], "Rick Wakeman")
        self.assertEqual(foo[0]["wp:foo_first_name"], "Rick")
        self.assertEqual(foo[0]["wp:foo_last_name"], "Wakeman")

        bar = getattr(cache, "wp:bar")
        self.assertIsInstance(bar, list)
        self.assertEqual(len(bar), 1)
        self.assertIsInstance(bar[0], dict)

        # values of the second item in the list
        self.assertEqual(bar[0]["wp:bar_id"], 12345)
        self.assertEqual(bar[0]["wp:bar_nicename"], "some-stuff")

        # the second item in the fixture <wp:bar> should not be cached
        with self.assertRaises(IndexError) as raises:
            bar[1]
        self.assertEqual(str(raises.exception), "list index out of range")


class WordpressImporterTestsCheckXmlTagsNotCached(TestCase):
    """
    This tests that the XML tags are not cached during an import because there
    is no settings.WORDPRESS_IMPORT_HOOKS_TAGS_TO_CACHE
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

    def test_xml_tags_not_cached(self):
        fragment = """
        <wp:foo>
            <wp:foo_id>3</wp:foo_id>
            <wp:foo_login>rickw</wp:foo_login>
            <wp:foo_email>rick@example.com</wp:foo_email>
            <wp:foo_display_name>Rick Wakeman</wp:foo_display_name>
            <wp:foo_first_name>Rick</wp:foo_first_name>
            <wp:foo_last_name>Wakeman</wp:foo_last_name>
        </wp:foo>
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
        built_file = generate_temporary_file(
            build_xml_stream(xml_tags_fragment=fragment).read()
        )

        self.process_import(built_file)

        # there should be one page imported
        self.assertEqual(self.imported_pages.count(), 1)
        self.assertEqual(self.imported_pages.first().title, "A title")

        # assertions for the content of tags_cache
        self.assertEqual(len(self.importer.tags_cache.__dict__.keys()), 0)
