import os

from bs4 import BeautifulSoup
from django.test import TestCase, override_settings

from wagtail_wordpress_import.prefilters.transform_styles_defaults import (
    transform_float_left,
    transform_float_right,
    transform_html_tag_em,
    transform_html_tag_strong,
    transform_style_bold,
    transform_style_center,
    transform_style_italic,
    transform_style_left,
    transform_style_right,
)
from wagtail_wordpress_import.prefilters.transform_styles_filter import (
    filter_transform_inline_styles,
    normalize_style_attrs,
)

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/fixtures"


class TestTransformStylesFilter(TestCase):
    def test_normalize_style_attrs(self):
        raw_html_file = open(f"{FIXTURES_PATH}/raw_html.txt", "r")
        soup = normalize_style_attrs(BeautifulSoup(raw_html_file, "html.parser"))
        span = soup.find("span")

        self.assertEqual(span.attrs["style"], "font-style:italic;font-weight:bold;")

    def test_filter_transform_inline_styles(self):
        input = open(f"{FIXTURES_PATH}/raw_html.txt", "r")
        output = filter_transform_inline_styles(input)
        soup = BeautifulSoup(output, "html.parser")

        """
        This is worthy of a note.
        <span style="font-weight: bold;font-style:italic;">Lorem ipsum (xcounterx) dolor sit amet</span>
        Gets transformed to
        <b><i>Lorem ipsum (xcounterx) dolor sit amet</i></b>
        Because the span has two specific styles.
        """
        first_tag = soup.find("b")
        self.assertEqual(first_tag.name, "b")

        with self.assertRaises(KeyError):
            self.assertTrue(first_tag.attrs["style"])

        first_tag_child = first_tag.find("i")
        self.assertEqual(first_tag_child.name, "i")
        self.assertEqual(first_tag_child.text, "Lorem ipsum (xcounterx) dolor sit amet")

        with self.assertRaises(KeyError):
            self.assertTrue(first_tag_child.attrs["style"])

        heading_tag = soup.find("h2")
        self.assertEqual(heading_tag.name, "h2")

        heading_tag_child = heading_tag.find("b")
        self.assertEqual(heading_tag_child.name, "b")
        self.assertIsNone(heading_tag_child.attrs.get("style"))

    def test_transform_style_bold(self):
        input = '<span style="font-weight: bold;">Text content</span>'
        soup = normalize_style_attrs(BeautifulSoup(input, "html.parser"))
        transform_style_bold(soup, soup.find("span"))
        bold = soup.find("b")
        span = soup.find("span")

        self.assertTrue(bold)
        self.assertFalse(span)

    def test_transform_style_italic(self):
        input = '<span style="font-style: italic;">Text content</span>'
        soup = normalize_style_attrs(BeautifulSoup(input, "html.parser"))
        transform_style_italic(soup, soup.find("span"))
        italic = soup.find("i")

        self.assertTrue(italic)

    def test_transform_style_center(self):
        input = '<p style="text-align: center;">Text content</p>'
        soup = normalize_style_attrs(BeautifulSoup(input, "html.parser"))
        transform_style_center(soup, soup.find("p"))
        paragraph = soup.find("p")

        self.assertTrue(paragraph)
        self.assertIn("align-center", paragraph.attrs["class"])

    def test_transform_style_left(self):
        input = '<p style="text-align: left;">Text content</p>'
        soup = normalize_style_attrs(BeautifulSoup(input, "html.parser"))
        transform_style_left(soup, soup.find("p"))
        paragraph = soup.find("p")

        self.assertTrue(paragraph)
        self.assertIn("align-left", paragraph.attrs["class"])

    def test_transform_style_right(self):
        input = '<p style="text-align: right;">Text content</p>'
        soup = normalize_style_attrs(BeautifulSoup(input, "html.parser"))
        transform_style_right(soup, soup.find("p"))
        paragraph = soup.find("p")

        self.assertTrue(paragraph)
        self.assertIn("align-right", paragraph.attrs["class"])

    def test_transform_float_left(self):
        input = '<p style="float: left;">Text content</p>'
        soup = normalize_style_attrs(BeautifulSoup(input, "html.parser"))
        transform_float_left(soup, soup.find("p"))
        paragraph = soup.find("p")

        self.assertTrue(paragraph)
        self.assertIn("float-left", paragraph.attrs["class"])

    def test_transform_float_right(self):
        input = '<p style="float: right;">Text content</p>'
        soup = normalize_style_attrs(BeautifulSoup(input, "html.parser"))
        transform_float_right(soup, soup.find("p"))
        paragraph = soup.find("p")

        self.assertTrue(paragraph)
        self.assertIn("float-right", paragraph.attrs["class"])

    def test_transform_html_tag_strong(self):
        input = "<strong>Text content</strong>"
        soup = BeautifulSoup(input, "html.parser")
        transform_html_tag_strong(soup, soup.find("strong"))
        strong = soup.find("b")

        self.assertTrue(strong)

    def test_transform_html_tag_em(self):
        input = "<em>Text content</em>"
        soup = BeautifulSoup(input, "html.parser")
        transform_html_tag_em(soup, soup.find("em"))
        italic = soup.find("i")

        self.assertTrue(italic)


def testing_transform_html_tag_blockquote(soup, tag):
    """
    a function to test as if passed in by a developer
    in their own config
    """
    tag.name = "div"


class TestTransformStylesFilterHtmlTagsDeveloperOverrides(TestCase):
    @override_settings(
        WAGTAIL_WORDPRESS_IMPORT_TRANSFORM_HTML_TAGS_MAPPING=[],
    )
    def test_filter_transform_html_tag_empty(self):
        input = "<em>Text content</em><strong>Text content</strong>"
        output = filter_transform_inline_styles(input)
        soup = BeautifulSoup(output, "html.parser")
        italic = soup.find("em")
        bold = soup.find("strong")

        self.assertTrue(italic)
        self.assertTrue(bold)

    @override_settings(
        WAGTAIL_WORDPRESS_IMPORT_TRANSFORM_HTML_TAGS_MAPPING=[
            ("strong", transform_html_tag_strong),
        ],
    )
    def test_filter_transform_html_tag_strong(self):
        input = "<em>Text content</em><strong>Text content</strong>"
        output = filter_transform_inline_styles(input)
        soup = BeautifulSoup(output, "html.parser")
        italic = soup.find("em")
        bold = soup.find("b")

        self.assertTrue(italic)
        self.assertTrue(bold)

    @override_settings(
        WAGTAIL_WORDPRESS_IMPORT_TRANSFORM_HTML_TAGS_MAPPING=[
            ("em", transform_html_tag_em),
        ],
    )
    def test_filter_transform_html_tag_em(self):
        input = "<em>Text content</em><strong>Text content</strong>"
        output = filter_transform_inline_styles(input)
        soup = BeautifulSoup(output, "html.parser")
        italic = soup.find("i")
        bold = soup.find("strong")

        self.assertTrue(italic)
        self.assertTrue(bold)

    @override_settings(
        WAGTAIL_WORDPRESS_IMPORT_TRANSFORM_HTML_TAGS_MAPPING=[
            ("strong", transform_html_tag_strong),
            ("em", transform_html_tag_em),
            ("blockquote", testing_transform_html_tag_blockquote),
        ],
    )
    def test_filter_transform_html_tag_bold(self):
        input = "<em>Text content</em><strong>Text content</strong><blockquote>Text content</blockquote>"
        output = filter_transform_inline_styles(input)
        soup = BeautifulSoup(output, "html.parser")
        italic = soup.find("i")
        bold = soup.find("b")
        div = soup.find("div")

        self.assertTrue(italic)
        self.assertTrue(bold)
        self.assertTrue(div)
