import os

from bs4 import BeautifulSoup
import bs4
from django.conf import settings
from django.test import TestCase, override_settings, modify_settings
from wagtail_wordpress_import.block_builder import BlockBuilder
from wagtail_wordpress_import.block_builder_defaults import (
    build_block_quote_block,
    build_form_block,
    build_heading_block,
    build_iframe_block,
    build_image_block,
    build_table_block,
    conf_domain_prefix,
    get_absolute_src,
    get_alignment_class,
    get_image_alt,
    get_image_file_name,
)
from wagtail_wordpress_import.prefilters.handle_shortcodes import BlockShortcodeHandler

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

    def test_remove_parent_tags_wagtail_block_caption(self):
        self.builder.promote_child_tags()
        output = self.output_remove_parent_tags

        wagtail_block_captions = output.find_all("wagtail_block_caption")
        for idx, wagtail_block_caption in enumerate(wagtail_block_captions):
            with self.subTest(
                f"Checking that both wagtail_block_caption tags are top level elements fixture:{idx}"
            ):
                self.assertTrue(
                    wagtail_block_caption.parent.name == self.expected_parent_name
                )

    @override_settings(
        WAGTAIL_WORDPRESS_IMPORTER_PROMOTE_CHILD_TAGS={
            "TAGS_TO_PROMOTE": ["iframe", "form", "blockquote"],
            "PARENTS_TO_REMOVE": ["p", "div", "span"],
        }
    )
    def test_promote_child_tags_has_registered_included_shortcodes(self):
        tags_to_promote = settings.WAGTAIL_WORDPRESS_IMPORTER_PROMOTE_CHILD_TAGS[
            "TAGS_TO_PROMOTE"
        ]
        self.builder.promote_child_tags()
        self.assertIn("wagtail_block_caption", tags_to_promote)


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

    # work in progress
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


@override_settings(BASE_URL="http://www.example.com")
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
        self.assertEqual(len(blocks), 3)

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
        self.assertEqual(len(blocks), 1)

    def test_richtext_block_3_content(self):
        """The expected content here should be lines 9 - 24 of raw_html.txt"""
        rich_text_content = BeautifulSoup(self.blocks[3]["value"], "html.parser")

        paragraph = rich_text_content.find("p")
        self.assertIsInstance(paragraph, bs4.element.Tag)

        list = rich_text_content.find("ul")
        self.assertIsInstance(list, bs4.element.Tag)

        heading_2 = rich_text_content.find("h2")
        self.assertIsInstance(heading_2, bs4.element.Tag)


class TestBlockBuilderDefaultsBaseUrl(TestCase):
    @override_settings(BASE_URL="http://www.example.com")
    def test_conf_domain_prefix(self):
        prefix = conf_domain_prefix()
        self.assertEqual(prefix, "http://www.example.com")

    @override_settings(WAGTAIL_WORDPRESS_IMPORTER_BASE_URL="http://www.example.com")
    def test_conf_domain_prefix(self):
        prefix = conf_domain_prefix()
        self.assertEqual(prefix, "http://www.example.com")

    @override_settings(
        BASE_URL="http://www.example.com",
        WAGTAIL_WORDPRESS_IMPORTER_BASE_URL="http://www.domain.com",
    )  # WAGTAIL_WORDPRESS_IMPORTER_BASE_URL takes preference
    def test_conf_domain_prefix(self):
        prefix = conf_domain_prefix()
        self.assertEqual(prefix, "http://www.domain.com")

    @override_settings()  # no BASE_URL or WAGTAIL_WORDPRESS_IMPORTER_BASE_URL
    def test_conf_domain_prefix_no_base_url_config(self):
        prefix = conf_domain_prefix()
        self.assertIsNone(prefix)


class TestRichTextImageLinking(TestCase):
    def test_images_linked_rich_text(self):
        """
        <p>Absolute image url.
            <a href="#">
                <img src="https://www.budgetsaresexy.com/images/bruno-4-runner.jpg" alt="">
            </a>
        </p>
        In the fixture file is the only one that will be converted.
        The other img tags will become image blocks
        """
        raw_html_file = """<p>Absolute image url.
            <a href="#">
                <img src="https://www.budgetsaresexy.com/images/bruno-4-runner.jpg" alt="">
            </a>
        </p>"""
        self.builder = BlockBuilder(raw_html_file, None, None)
        self.builder.promote_child_tags()
        self.blocks = self.builder.build()

        self.assertEqual(self.blocks[0]["type"], "rich_text")

        value_soup = BeautifulSoup(self.blocks[0]["value"], "html.parser")
        # embed_id is an image id. it should be returned as an integer but we cannot
        # rely on the value returned here so check if it is an integer.
        # there is a ticket to improve testing when fetching remote images:
        # https://projects.torchbox.com/projects/wordpress-to-wagtail-importer-package/tickets/76
        embed_id = int(value_soup.find("embed").attrs["id"])
        self.assertIsInstance(embed_id, int)

    def test_get_image_alt(self):
        input = get_soup(
            '<img src="fakeimage.jpg" alt="image alt" />', "html.parser"
        ).find("img")
        self.assertEqual(get_image_alt(input), "image alt")

    def test_get_image_file_name(self):
        self.assertEqual(get_image_file_name("fakeimage.jpg"), "fakeimage.jpg")
        self.assertEqual(get_image_file_name("folder/fakeimage.jpg"), "fakeimage.jpg")
        self.assertEqual(
            get_image_file_name("http://www.example.com/folder1/folder2/fakeimage.jpg"),
            "fakeimage.jpg",
        )

    def test_get_absolute_src(self):
        self.assertEqual(
            get_absolute_src("fakeimage.jpg", "http://www.example.com"),
            "http://www.example.com/fakeimage.jpg",
        )
        self.assertEqual(
            get_absolute_src("folder/fakeimage.jpg", "http://www.example.com"),
            "http://www.example.com/folder/fakeimage.jpg",
        )

    def test_get_absolute_src_without_base_url(self):
        self.assertEqual(
            get_absolute_src("folder/fakeimage.jpg"),
            "folder/fakeimage.jpg",
        )

    def test_get_abolute_src_slashes_at_start(self):
        self.assertEqual(
            get_absolute_src("//folder/fakeimage.jpg", "http://www.example.com"),
            "http://www.example.com/folder/fakeimage.jpg",
        )

    def test_get_alignment_class_align_left(self):
        soup = get_soup(
            '<img src="fakeimage.jpg" alt="image alt" class="align-left" />',
            "html.parser",
        ).find("img")
        self.assertEqual(get_alignment_class(soup), "left")

    def test_get_alignment_class_align_right(self):
        soup = get_soup(
            '<img src="fakeimage.jpg" alt="image alt" class="align-right" />',
            "html.parser",
        ).find("img")
        self.assertEqual(get_alignment_class(soup), "right")

    def test_get_alignment_class_not_present(self):
        soup = get_soup(
            '<img src="fakeimage.jpg" alt="image alt" />',
            "html.parser",
        ).find("img")
        self.assertEqual(get_alignment_class(soup), "fullwidth")

    """
    TODO: Add some more tests
    I need to include tests here for images and documents.
    I'm not sure how this could be done at the moment.
    Also applies to: test_images_linked_rich_text() above
    """
