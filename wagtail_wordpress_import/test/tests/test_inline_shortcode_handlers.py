from re import Match
from django.test import TestCase

from wagtail_wordpress_import.handle_inline_shortcodes import InlineShortcodeHandler


class TestInlineShortcodeHandler(TestCase):
    def test_regex_has_matches(self):
        class FooHandler(InlineShortcodeHandler):
            shortcode_name = "foo"

            def construct_html_tag(self, html):
                return self._pattern.finditer(html)

        handler = FooHandler()
        html = """[foo bar="1"]
        [bar foo="1"]"""

        out = handler.construct_html_tag(html)
        self.assertEqual(sum(1 for _ in out), 1)

    def test_regex_has_no_matches(self):
        class FooHandler(InlineShortcodeHandler):
            shortcode_name = "nomatch"

            def construct_html_tag(self, html):
                return self._pattern.finditer(html)

        handler = FooHandler()
        html = """[foo bar="1"]
        [bar foo="1"]"""

        out = handler.construct_html_tag(html)
        self.assertEqual(sum(1 for _ in out), 0)

    def test_get_shortcode_attrs(self):
        class FooHandler(InlineShortcodeHandler):
            shortcode_name = "foo"

        handler = FooHandler()
        attrs = 'foo="1" bar="2"'

        attrs = handler.get_shortcode_attrs(attrs)
        self.assertEqual(attrs, {"foo": "1", "bar": "2"})
