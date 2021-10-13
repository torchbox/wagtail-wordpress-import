import json
from django.test import TestCase
from wagtail_wordpress_import.block_builder import check_image_src, BlockBuilder
from wagtail_wordpress_import.logger import Logger


class TestBlockBuilder(TestCase):
    def setUp(self):
        self.protocol = "https://"
        self.image_src = "commons.wikimedia.org/wiki/Category:Image_placeholders#/media/File:Male_Avatar.jpg"
        self.full_url = self.protocol + self.image_src
        self.domain_prefix = "https://www.budgetsaresexy.com/"
        self.image_tag = f"""<img src="{self.full_url}" />"""

    def test_check_image_src(self):
        """
        this test image src values of the known type encountered
        1. no value in src
        2. relative image in src
        3. full image path in src
        """
        image_with_full_url = self.full_url
        self.assertEqual(check_image_src(image_with_full_url), self.full_url)

        image_src_is_relative = self.image_src
        self.assertEqual(
            check_image_src(image_src_is_relative), self.domain_prefix + self.image_src
        )

        image_src_is_blank = ""
        self.assertEqual(check_image_src(image_src_is_blank), self.domain_prefix)

    def test_block_builder_run(self):
        """
        this test the builder run method by passing in a html string
        and checking the blocks dict output is in the correct order with
        the correct block types
        """
        fake_node = {"wp:post_id": "20"}
        fake_logger = Logger("fake_dir")
        value = """
        <p><b>lorem</b></p>
        <p>lorem</p>
        <p>lorem</p>
        <iframe></iframe>
        <p>lorem</p>
        <p>lorem</p>
        <h1>lorem</h1>
        <p>lorem</p>
        <h2>lorem</h2>
        <table><tr><td>lorem</td></tr></table>
        <form><button>Submit</button></form>
        <blockquote cite="writers name"><p>lorem</p></blockquote>
        """
        builder = BlockBuilder(
            value,
            fake_node,
            fake_logger,
        )
        out = builder.build()

        self.assertEqual(out[0]["type"], "rich_text")
        self.assertEqual(
            out[0]["value"], """<p><b>lorem</b></p><p>lorem</p><p>lorem</p>"""
        )

        self.assertEqual(out[1]["type"], "raw_html")
        self.assertEqual(
            out[1]["value"],
            """<div class="core-custom"><div class="responsive-iframe"><iframe></iframe></div></div>""",
        )

        self.assertEqual(out[2]["type"], "rich_text")
        self.assertEqual(
            out[2]["value"],
            """<p>lorem</p><p>lorem</p>""",
        )

        self.assertEqual(out[3]["type"], "heading")
        self.assertEqual(
            out[3]["value"]["importance"],
            """h1""",
        )
        self.assertEqual(
            out[3]["value"]["text"],
            """lorem""",
        )

        self.assertEqual(out[4]["type"], "rich_text")
        self.assertEqual(out[4]["value"], """<p>lorem</p>""")

        self.assertEqual(out[5]["type"], "heading")
        self.assertEqual(
            out[5]["value"]["importance"],
            """h2""",
        )
        self.assertEqual(
            out[5]["value"]["text"],
            """lorem""",
        )

        self.assertEqual(out[6]["type"], "raw_html")
        self.assertEqual(
            out[6]["value"],
            """<table><tr><td>lorem</td></tr></table>""",
        )

        self.assertEqual(out[7]["type"], "raw_html")
        self.assertEqual(
            out[7]["value"],
            """<form><button>Submit</button></form>""",
        )

        self.assertEqual(out[8]["type"], "block_quote")
        self.assertEqual(
            out[8]["value"]["quote"],
            """lorem""",
        )
        self.assertEqual(out[8]["value"]["attribution"], "writers name")
