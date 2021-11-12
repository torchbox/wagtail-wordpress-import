from io import StringIO
from xml.dom import pulldom
from django.test import TestCase, override_settings
from wagtail_wordpress_import.importers.importer_hooks import (
    import_hooks_xml_tags_to_cache,
)
from wagtail_wordpress_import.logger import Logger
from wagtail_wordpress_import.importers.wordpress import WordpressImporter
from wagtail_wordpress_import.xml_boilerplate import (
    build_xml_stream,
)


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
