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

    def test_regex_mathes_adjacent_first_place(self):
        class FooHandler(InlineShortcodeHandler):
            shortcode_name = "foo"

            def construct_html_tag(self, html):
                return self._pattern.finditer(html)

        handler = FooHandler()
        html = """[foo bar="1"][bar foo="1"]"""

        out = handler.construct_html_tag(html)
        self.assertEqual(sum(1 for _ in out), 1)

    def test_regex_mathes_adjacent_content_between(self):
        class FooHandler(InlineShortcodeHandler):
            shortcode_name = "bar"

            def construct_html_tag(self, html):
                return self._pattern.finditer(html)

        handler = FooHandler()
        html = """[foo bar="1"]content between[bar foo="1"]"""

        out = handler.construct_html_tag(html)
        self.assertEqual(sum(1 for _ in out), 1)

    def test_regex_mathes_adjacent_content_around(self):
        class FooHandler(InlineShortcodeHandler):
            shortcode_name = "bar"

            def construct_html_tag(self, html):
                return self._pattern.finditer(html)

        handler = FooHandler()
        html = """content before[foo bar="1"][bar foo="1"]content after"""

        out = handler.construct_html_tag(html)
        self.assertEqual(sum(1 for _ in out), 1)


class TestInlineShortcodeHandlerDocumentedExample(TestCase):
    def test_construct_html_tag_documented_example(self):
        class FooHandler(InlineShortcodeHandler):
            shortcode_name = "foo"

            def construct_html_tag(self, html):
                matches = self._pattern.finditer(html)
                for match in matches:
                    attrs = self.get_shortcode_attrs(match.groupdict()["attrs"])
                    html = html.replace(
                        match.group(),
                        f'<{self.element_name} data-{self.shortcode_name}="{attrs["symbol"]}">${attrs["symbol"]}</{self.element_name}>',
                    )

                return html

        handler = FooHandler()
        html = """some content before [foo symbol="ABC"] some content after"""

        out = handler.construct_html_tag(html)
        self.assertEqual(
            out,
            'some content before <span data-foo="ABC">$ABC</span> some content after',
        )

    def test_construct_html_tag_documented_example_ignores_bar(self):
        class FooHandler(InlineShortcodeHandler):
            shortcode_name = "foo"

            def construct_html_tag(self, html):
                matches = self._pattern.finditer(html)
                for match in matches:
                    attrs = self.get_shortcode_attrs(match.groupdict()["attrs"])
                    html = html.replace(
                        match.group(),
                        f'<{self.element_name} data-{self.shortcode_name}="{attrs["symbol"]}">${attrs["symbol"]}</{self.element_name}>',
                    )

                return html

        handler = FooHandler()
        html = """some content before [foo symbol="ABC"] some content after [bar baz="foo"]"""

        out = handler.construct_html_tag(html)
        self.assertEqual(
            out,
            'some content before <span data-foo="ABC">$ABC</span> some content after [bar baz="foo"]',
        )


class TestGetAttrs(TestCase):
    def test_get_shortcode_attrs(self):
        class FooHandler(InlineShortcodeHandler):
            shortcode_name = "foo"

        handler = FooHandler()
        attrs = 'foo="1" bar="2"'

        attrs = handler.get_shortcode_attrs(attrs)
        self.assertEqual(attrs, {"foo": "1", "bar": "2"})

    def test_get_shortcode_attrs_missing_quotes(self):
        class FooHandler(InlineShortcodeHandler):
            shortcode_name = "foo"

        handler = FooHandler()
        attrs = 'foo="1" bar=2'

        attrs = handler.get_shortcode_attrs(attrs)
        self.assertEqual(attrs, {"foo": "1", "bar": "2"})

    def test_get_shortcode_attrs_no_quotes(self):
        class FooHandler(InlineShortcodeHandler):
            shortcode_name = "foo"

        handler = FooHandler()
        attrs = "foo=1 bar=2"

        attrs = handler.get_shortcode_attrs(attrs)
        self.assertEqual(attrs, {"foo": "1", "bar": "2"})

    def test_get_shortcode_attrs_extra_spacing(self):
        class FooHandler(InlineShortcodeHandler):
            shortcode_name = "foo"

        handler = FooHandler()
        attrs = " foo=1  bar=2 "

        with self.subTest(
            """The provided method cannot handle multiple spaces around
            the attrs or multiple space between the attrs"""
        ):
            with self.assertRaises(IndexError):
                attrs = handler.get_shortcode_attrs(attrs)
