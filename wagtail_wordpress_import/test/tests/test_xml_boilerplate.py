from io import StringIO

from django.test import TestCase

from wagtail_wordpress_import.test.tests.xml_boilerplate import (
    build_xml_stream,
    xml_stream_footer,
    xml_stream_header,
)


class TestXmlStream(TestCase):
    def test_building_xml_stream(self):
        """This is just a test that our in-class fixture builder works okay.
        This unit test is a bit sensitive of blank lines and indentation, but the rest
        don't really matter so long as we format valid XML.
        """
        fragment_tags = """
                <wp:foo>
                    <wp:foo_first_name>J.</wp:foo_first_name>
                    <wp:foo_last_name>Money</wp:foo_last_name>
                </wp:foo>"""
        fragment_items = """"""
        built = build_xml_stream(
            xml_tags_fragment=fragment_tags, xml_items_fragment=fragment_items
        ).read()
        expected = StringIO(
            xml_stream_header
            + """
                <wp:foo>
                    <wp:foo_first_name>J.</wp:foo_first_name>
                    <wp:foo_last_name>Money</wp:foo_last_name>
                </wp:foo>"""
            + xml_stream_footer
        ).read()
        self.maxDiff = None
        self.assertEqual(built, expected)
