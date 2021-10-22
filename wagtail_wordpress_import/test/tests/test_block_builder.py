import os

from bs4 import BeautifulSoup
from django.test import TestCase
from wagtail_wordpress_import.block_builder import BlockBuilder, check_image_src
from wagtail_wordpress_import.block_builder_defaults import (
    build_block_quote_block,
    build_form_block,
    build_heading_block,
    build_iframe_block,
    build_image_block,
    build_table_block,
)

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/fixtures"


def get_soup(html, parser):
    soup = BeautifulSoup(html, parser)
    return soup


class TestBlockBuilderRemoveParents(TestCase):
    def setUp(self):
        raw_html_file = open(f"{FIXTURES_PATH}/raw_html.txt", "r")
        self.builder = BlockBuilder(raw_html_file, None, None)
        self.builder.promote_child_tags()
        self.output_remove_parent_tags = self.builder.soup
        self.expected_parent_name = "body"

    def test_remove_parent_tags_iframe(self):
        output = self.output_remove_parent_tags

        iframe = output.find("iframe", {"data-testing": "hasnoparent"})
        self.assertTrue(iframe.parent.name == self.expected_parent_name)

        iframe = output.find("iframe", {"data-testing": "hasparent"})
        self.assertTrue(iframe.parent.name == self.expected_parent_name)

    def test_remove_parent_tags_form(self):
        output = self.output_remove_parent_tags

        form = output.find("form", attrs={"data-testing": "hasnoparent"})
        self.assertTrue(form.parent.name == self.expected_parent_name)

        form = output.find("form", attrs={"data-testing": "hasparent"})
        self.assertTrue(form.parent.name == self.expected_parent_name)

    def test_remove_parent_tags_blockquote(self):
        output = self.output_remove_parent_tags

        blockquote = output.find("blockquote", attrs={"data-testing": "hasnoparent"})
        self.assertTrue(blockquote.parent.name == self.expected_parent_name)

        blockquote = output.find("blockquote", attrs={"data-testing": "hasparent"})
        self.assertTrue(blockquote.parent.name == self.expected_parent_name)


class TestBlockBuilderBlockDefaults(TestCase):
    def test_build_block_quote_block(self):
        input = """<blockquote data-testing="no-parent" cite="http://www.example.com">
        Lorem ipsum dolor sit amet.
        </blockquote>"""

        output = build_block_quote_block(get_soup(input, "html.parser"))
        self.assertEqual(output["type"], "block_quote")
        self.assertIsInstance(output["value"], dict)
        self.assertTrue(output["value"]["quote"].startswith("Lorem"))

    def test_build_form_block(self):
        input = """<form data-testing="no-parent"><button>Submit</button></form>"""

        output = build_form_block(get_soup(input, "html.parser"))
        self.assertEqual(output["type"], "raw_html")
        self.assertTrue(output["value"].startswith("<form"))

    def test_build_heading_block(self):
        input = """<h1>A heading 1</h1>"""
        soup = get_soup(input, "html.parser").find("h1")
        output = build_heading_block(soup)
        self.assertEqual(output["type"], "heading")
        self.assertEqual(output["value"]["importance"], "h1")

    def test_build_iframe_block(self):
        input = """<iframe src="https://www.youtube.com/embed/CQ7Gx8b7ac4" width="560" height="315" frameborder="0" allowfullscreen="allowfullscreen" data-testing="no-parent"></iframe>"""

        output = build_iframe_block(get_soup(input, "html.parser"))
        self.assertEqual(output["type"], "raw_html")
        self.assertTrue(output["value"].startswith("<div"))

    def test_build_image_block(self):
        input = """<img src="http://www.example.com/image.jpg" />"""
        soup = get_soup(input, "html.parser")
        output = build_image_block(soup)
        self.assertEqual(output["type"], "image")
        self.assertEqual(output["value"], 1)

    def test_build_table_block(self):
        input = """<table id="tablepress-1" class="tablepress tablepress-id-1 dataTable"><caption>&#160;</caption>
            <thead>
            <tr class="row-1 odd">
            <th class="column-1 sorting_disabled" colspan="1" rowspan="1">Item</th>
            <th class="column-2 sorting_disabled" colspan="1" rowspan="1">Amount</th>
            </tr>
            </thead>
            <tfoot>
            <tr class="row-35 odd">
            <th class="column-1" colspan="1" rowspan="1">TOTAL:</th>
            <th class="column-2" colspan="1" rowspan="1">$1,127.67</th>
            </tr>
            </tfoot>
            <tbody class="row-hover">
            <tr class="row-2 even">
            <td class="column-1">Lorem 1</td>
            <td class="column-2">Lorem 1/1</td>
            </tr>
            <tr class="row-3 odd">
            <td class="column-1">Lorem 2</td>
            <td class="column-2">Lorem 2/1</td>
            </tr>
            </tbody>
            </table>"""

        output = build_table_block(get_soup(input, "html.parser"))
        self.assertEqual(output["type"], "raw_html")
        self.assertTrue(output["value"].startswith("<table"))


class TestBlockBuilderBuild(TestCase):
    def setUp(self):
        raw_html_file = open(f"{FIXTURES_PATH}/raw_html.txt", "r")
        self.builder = BlockBuilder(raw_html_file, None, None)
        self.builder.promote_child_tags()
        self.blocks = self.builder.build()

    def test_rich_text_blocks_count(self):
        blocks = [
            block["type"] for block in self.blocks if block["type"] == "rich_text"
        ]
        self.assertEqual(len(blocks), 2)

    def test_blockquote_blocks_count(self):
        blocks = [
            block["type"] for block in self.blocks if block["type"] == "block_quote"
        ]
        self.assertEqual(len(blocks), 2)

    def test_raw_html_blocks_count(self):
        blocks = [block["type"] for block in self.blocks if block["type"] == "raw_html"]
        self.assertEqual(len(blocks), 5)

    def test_heading_blocks_count(self):
        blocks = [block["type"] for block in self.blocks if block["type"] == "heading"]
        self.assertEqual(len(blocks), 2)
