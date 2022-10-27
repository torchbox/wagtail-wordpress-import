import os

import bs4
import requests
import responses
from bs4 import BeautifulSoup
from django.test import TestCase, override_settings
from wagtail.images import get_image_model

from wagtail_wordpress_import.block_builder import BlockBuilder, conf_promote_child_tags
from wagtail_wordpress_import.block_builder_defaults import (
    build_block_quote_block,
    build_form_block,
    build_heading_block,
    build_iframe_block,
    build_image_block,
    build_table_block,
    fetch_url,
    get_absolute_src,
    get_alignment_class,
    get_image_alt,
    get_image_file_name,
    image_linker,
)
from wagtail_wordpress_import.test.tests.utility_functions import (
    get_soup,
    mock_image,
    mock_pdf,
)

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/fixtures"


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

    def test_conf_promote_child_tags(self):
        conf = conf_promote_child_tags()
        self.assertIn("iframe", conf["TAGS_TO_PROMOTE"])
        self.assertIn("form", conf["TAGS_TO_PROMOTE"])
        self.assertIn("blockquote", conf["TAGS_TO_PROMOTE"])

    def test_conf_promote_child_tags_includes_shortcodes_html_tags(self):
        conf = conf_promote_child_tags()
        self.assertIn("wagtail_block_caption", conf["TAGS_TO_PROMOTE"])


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


@override_settings(WAGTAIL_WORDPRESS_IMPORTER_SOURCE_DOMAIN="http://www.example.com")
class TestBlockBuilderBuild(TestCase):
    @responses.activate
    def setUp(self):
        responses.add(
            responses.GET,
            "https://www.example.com/images/bruno-4-runner.jpg",
            body=mock_image().read(),
            status=200,
            content_type="image/jpeg",
        )
        responses.add(
            responses.GET,
            "https://www.example.com/files/personal-finance-culminating-assignment.pdf",
            body=mock_pdf(),
            status=200,
            content_type="application/pdf",
        )
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

    def test_richtext_block_6_content(self):
        """The expected content here should be lines 18 - 31 of raw_html.txt"""
        rich_text_content = BeautifulSoup(self.blocks[6]["value"], "html.parser")

        paragraph = rich_text_content.find("p")
        self.assertIsInstance(paragraph, bs4.element.Tag)

        list = rich_text_content.find("ul")
        self.assertIsInstance(list, bs4.element.Tag)

        heading_2 = rich_text_content.find("h2")
        self.assertIsInstance(heading_2, bs4.element.Tag)


@override_settings(WAGTAIL_WORDPRESS_IMPORTER_SOURCE_DOMAIN="http://www.example.com")
class TestRichTextImageLinking(TestCase):
    @responses.activate
    def test_embed_tag_generated_all_attrs(self):
        raw_html_file = """
        <p>
        <a href="https://www.example.com/images/bruno-4-runner.jpg">
        <img src="https://www.example.com/images/bruno-4-runner.jpg" alt="bruno 4 runner">
        </a>
        </p>
        """
        responses.add(
            responses.GET,
            "https://www.example.com/images/bruno-4-runner.jpg",
            body=mock_image().read(),
            status=200,
            content_type="image/jpeg",
        )
        output = image_linker(raw_html_file)
        image = get_image_model().objects.get(title="bruno-4-runner.jpg")
        soup = BeautifulSoup(output, "html.parser")
        embed_tag = soup.find("embed")

        with self.subTest("embed tag attr 'id' has the correct ID"):
            self.assertEqual(embed_tag.attrs["id"], str(image.id))

        with self.subTest("embed tag attr 'embedtype' has the correct type"):
            self.assertEqual(embed_tag.attrs["embedtype"], "image")

        with self.subTest("embed tag attr 'format' has correct style format"):
            self.assertEqual(embed_tag.attrs["format"], "fullwidth")

        with self.subTest("embed tag attr 'alt' has correct content"):
            self.assertEqual(embed_tag.attrs["alt"], "bruno 4 runner")

    @responses.activate
    def test_embed_tag_generated_class_align_left(self):
        raw_html_file = """
        <p>
        <a href="https://www.example.com/images/bruno-4-runner.jpg">
        <img src="https://www.example.com/images/bruno-4-runner.jpg" alt="bruno 4 runner" class="align-left">
        </a>
        </p>
        """
        responses.add(
            responses.GET,
            "https://www.example.com/images/bruno-4-runner.jpg",
            body=mock_image().read(),
            status=200,
            content_type="image/jpeg",
        )
        output = image_linker(raw_html_file)
        image = get_image_model().objects.get(title="bruno-4-runner.jpg")
        soup = BeautifulSoup(output, "html.parser")
        embed_tag = soup.find("embed")
        self.assertEqual(embed_tag.attrs["id"], str(image.id))
        self.assertEqual(embed_tag.attrs["embedtype"], "image")
        self.assertEqual(embed_tag.attrs["format"], "left")
        self.assertEqual(embed_tag.attrs["alt"], "bruno 4 runner")

    @responses.activate
    def test_embed_tag_generated_class_align_right(self):
        raw_html_file = """
        <p>
        <a href="https://www.example.com/images/bruno-4-runner.jpg">
        <img src="https://www.example.com/images/bruno-4-runner.jpg" alt="bruno 4 runner" class="align-right">
        </a>
        </p>
        """
        responses.add(
            responses.GET,
            "https://www.example.com/images/bruno-4-runner.jpg",
            body=mock_image().read(),
            status=200,
            content_type="image/jpeg",
        )
        output = image_linker(raw_html_file)
        image = get_image_model().objects.get(title="bruno-4-runner.jpg")
        soup = BeautifulSoup(output, "html.parser")
        embed_tag = soup.find("embed")
        self.assertEqual(embed_tag.attrs["id"], str(image.id))
        self.assertEqual(embed_tag.attrs["embedtype"], "image")
        self.assertEqual(embed_tag.attrs["format"], "right")
        self.assertEqual(embed_tag.attrs["alt"], "bruno 4 runner")


class TestBlockBuilderUtilityMethods(TestCase):
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


class TestBlockBuilderFetchUrlRequests(TestCase):
    def setUp(self):
        self.image_url = "http://example.com/no-image.jpg"
        self.page_url = "http://example.com/no-page.html"

    @responses.activate
    def test_fetch_url_success(self):
        responses.add(
            responses.GET,
            self.image_url,
            body=mock_image().read(),
            status=200,
            content_type="image/jpegs",
        )
        response, status, content_type = fetch_url(self.image_url)
        self.assertTrue(response.content.startswith(b"\xff\xd8"))
        self.assertTrue(status)
        self.assertTrue("image/jpeg" in content_type)

    @responses.activate
    def test_fetch_url_raises_connection_error(self):
        responses.add(
            responses.GET,
            self.page_url,
            body=requests.ConnectionError(),
        )
        self.assertTrue(
            fetch_url(self.page_url),
            (None, True, None),
        )

    @responses.activate
    def test_fetch_url_raises_http_error(self):
        responses.add(
            responses.GET,
            self.page_url,
            body=requests.HTTPError(),
        )
        self.assertTrue(
            fetch_url(self.page_url),
            (None, True, None),
        )

    @responses.activate
    def test_fetch_url_raises_request_exception(self):
        responses.add(
            responses.GET,
            self.page_url,
            body=requests.RequestException(),
        )
        self.assertTrue(
            fetch_url(self.page_url),
            (None, True, None),
        )

    @responses.activate
    def test_fetch_url_raises_read_timeout(self):
        responses.add(
            responses.GET,
            self.page_url,
            body=requests.ReadTimeout(),
        )
        self.assertTrue(
            fetch_url(self.page_url),
            (None, True, None),
        )

    @responses.activate
    def test_fetch_url_raises_timeout(self):
        responses.add(
            responses.GET,
            self.page_url,
            body=requests.Timeout(),
        )
        self.assertTrue(
            fetch_url(self.page_url),
            (None, True, None),
        )

    @responses.activate
    def test_fetch_url_raises_connect_timeout(self):
        responses.add(
            responses.GET,
            self.page_url,
            body=requests.ConnectTimeout(),
        )
        self.assertTrue(
            fetch_url(self.page_url),
            (None, True, None),
        )
