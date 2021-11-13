import os
from io import StringIO
from xml.dom import pulldom

from django.test import TestCase, override_settings
from wagtail.core.models import Page
from wagtail_wordpress_import.importers.importer_hooks import (
    import_hooks_xml_tags_to_cache,
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


class TestImportHooksOverrideConfig(TestCase):
    @override_settings(WORDPRESS_IMPORT_HOOKS_TAGS_TO_CACHE=["wp:foo"])
    def test_persist_tags_config(self):
        self.assertEqual(import_hooks_xml_tags_to_cache(), ["wp:foo"])


@override_settings(WORDPRESS_IMPORT_HOOKS_TAGS_TO_CACHE=["wp:foo", "wp:bar"])
class TestImportHooksXmlTagPersisted(TestCase):
    def setUp(self):
        self.logger = Logger("foo")
        self.tags_cache = None

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
            self.tags_cache = self.importer.cache_xml_tags(event, node, xml_doc)

        return self.tags_cache

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

        self.assertIsInstance(cache.foo, list)
        self.assertEqual(len(cache.foo), 1)

        # values of the first item in the list
        foo = cache.foo[0]
        self.assertEqual(foo["wp:foo_id"], 3)
        self.assertEqual(foo["wp:foo_login"], "rickw")
        self.assertEqual(foo["wp:foo_email"], "rick@example.com")
        self.assertEqual(foo["wp:foo_display_name"], "Rick Wakeman")
        self.assertEqual(foo["wp:foo_first_name"], "Rick")
        self.assertEqual(foo["wp:foo_last_name"], "Wakeman")

        self.assertIsInstance(cache.bar, list)
        self.assertEqual(len(cache.bar), 1)

        # values of the second item in the list
        bar = cache.bar[0]
        self.assertEqual(bar["wp:bar_id"], 12345)
        self.assertEqual(bar["wp:bar_nicename"], "some-stuff")

        # the second item in the fixture <wp:bar> should not be cached
        with self.assertRaises(KeyError) as raises:
            error = bar[1]
        self.assertEqual(str(raises.exception), "1")


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
        built_file = generate_temporay_file(
            build_xml_stream(xml_tags_fragment=fragment).read()
        )

        self.process_import(built_file)

        # there should be one page imported
        self.assertEqual(self.imported_pages.count(), 1)
        self.assertEqual(self.imported_pages.first().title, "A title")

        # assertions for the content of tags_cache is done in
        #
        self.assertEqual(len(self.importer.tags_cache.__dict__.keys()), 0)


@override_settings(WORDPRESS_IMPORT_HOOKS_TAGS_TO_CACHE=["wp:foo", "wp:bar"])
class WordpressImporterTestsCheckXmlTagsNotCached(TestCase):
    """
    This tests that the XML tags are cached during an import because
    settings.WORDPRESS_IMPORT_HOOKS_TAGS_TO_CACHE is set
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
        built_file = generate_temporay_file(
            build_xml_stream(xml_tags_fragment=fragment).read()
        )

        self.process_import(built_file)

        # there should be one page imported
        self.assertEqual(self.imported_pages.count(), 1)
        self.assertEqual(self.imported_pages.first().title, "A title")

        self.assertEqual(len(self.importer.tags_cache.__dict__.keys()), 2)
