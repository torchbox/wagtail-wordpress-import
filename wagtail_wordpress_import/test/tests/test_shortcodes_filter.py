import os

from bs4 import BeautifulSoup
from django.test import TestCase

from wagtail_wordpress_import.prefilters.shortcodes import BlockShortcodeHandler

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/fixtures"


class TestShortcodesRegex(TestCase):
    def test_shortcode_is_found(self):
        class FooHandler(BlockShortcodeHandler):
            tag_name = "foo"

        handler = FooHandler()
        html = "foo[foo]baz[/foo]quux"

        match = handler._pattern.search(html)
        self.assertEqual(match.start(), 3)
        self.assertEqual(match.end(), 17)
        self.assertEqual(match.group("content"), "baz")
        self.assertEqual(match.group("attrs"), "")

    def test_multiple_shortcodes_are_found(self):
        class FooHandler(BlockShortcodeHandler):
            tag_name = "foo"

        handler = FooHandler()
        html = 'foo[foo]baz[/foo]quux[foo width="12"]spam[/foo]eggs'

        matches = list(handler._pattern.finditer(html))

        self.assertEqual(matches[0].start(), 3)
        self.assertEqual(matches[0].end(), 17)
        self.assertEqual(matches[0].group("content"), "baz")
        self.assertEqual(matches[0].group("attrs"), "")
        self.assertEqual(matches[1].start(), 21)
        self.assertEqual(matches[1].end(), 47)
        self.assertEqual(matches[1].group("content"), "spam")
        self.assertEqual(matches[1].group("attrs"), ' width="12"')

    def test_content_can_contain_square_brackets(self):
        class FooHandler(BlockShortcodeHandler):
            tag_name = "foo"

        handler = FooHandler()
        html = "embalmed ones[foo][stray dogs][/foo]"

        match = handler._pattern.search(html)

        self.assertEqual(match.start(), 13)
        self.assertEqual(match.end(), 36)
        self.assertEqual(
            match.group("content"), "[stray dogs]",
        )
        self.assertEqual(match.group("attrs"), "")


class TestShortcodesSubstitution(TestCase):
    fodder = (
        "This is a block of text preceding the caption.\n\n"
        '[caption id="attachment_46162" align="aligncenter" width="600"]'
        '<img class="wp-image-46162 size-full" '
        'src="https://www.example.com/images/foo.jpg" '
        'alt="This describes the image" width="600" height="338" /> '
        "<em>[This is a caption about the image (the one above) in "
        '<a href="https//www.example.com/bar/" target="_blank" '
        'rel="noopener noreferrer">Glorious Rich Text</a>!]</em>[/caption]'
        "<strong>The following text is surrounded by strong tags.</strong>"
    )

    def test_basic(self):
        class FooHandler(BlockShortcodeHandler):
            tag_name = "foo"

        html = "ham[foo]eggs[/foo]spam"
        handler = FooHandler()
        html = handler.pre_filter(html)
        self.assertEqual(html, "ham<wagtail_block_foo>eggs</wagtail_block_foo>spam")

    def test_shortcode_at_the_start_of_a_string(self):
        class FooHandler(BlockShortcodeHandler):
            tag_name = "foo"

        html = "[foo]radiators[/foo]jam"
        handler = FooHandler()
        html = handler.pre_filter(html)
        self.assertEqual(html, "<wagtail_block_foo>radiators</wagtail_block_foo>jam")

    def test_beautifulsoup_can_parse(self):
        class FooHandler(BlockShortcodeHandler):
            tag_name = "foo"

        html = "ham[foo]eggs[/foo]spam"
        handler = FooHandler()
        html = handler.pre_filter(html)
        soup = BeautifulSoup(html, "html.parser")
        tags = soup.find_all(True)
        self.assertEqual(len(tags), 1)
        self.assertEqual(str(tags[0]), "<wagtail_block_foo>eggs</wagtail_block_foo>")

    def test_caption(self):
        class CaptionHandler(BlockShortcodeHandler):
            tag_name = "caption"

        html = 'Some pretext[caption width="100"]The content of the tag[/caption]'
        handler = CaptionHandler()
        html = handler.pre_filter(html)
        self.assertEqual(
            html,
            'Some pretext<wagtail_block_caption width="100">The content of the tag</wagtail_block_caption>',
        )

    def test_known_content(self):
        class CaptionHandler(BlockShortcodeHandler):
            tag_name = "caption"

        html = (
            "This is a block of text preceding the caption.\n\n"
            '[caption id="attachment_46162" align="aligncenter" width="600"]'
            '<img class="wp-image-46162 size-full" '
            'src="https://www.example.com/images/foo.jpg" '
            'alt="This describes the image" width="600" height="338" /> '
            "<em>[This is a caption about the image (the one above) in "
            '<a href="https//www.example.com/bar/" target="_blank" '
            'rel="noopener noreferrer">Glorious Rich Text</a>!]</em>'
            "[/caption]"
            "<strong>The following text is surrounded by strong tags.</strong>"
        )
        handler = CaptionHandler()
        html = handler.pre_filter(html)
        self.assertEqual(
            html,
            "This is a block of text preceding the caption.\n\n"
            '<wagtail_block_caption id="attachment_46162" align="aligncenter" width="600">'
            '<img class="wp-image-46162 size-full" '
            'src="https://www.example.com/images/foo.jpg" '
            'alt="This describes the image" width="600" height="338" /> '
            "<em>[This is a caption about the image (the one above) in "
            '<a href="https//www.example.com/bar/" target="_blank" '
            'rel="noopener noreferrer">Glorious Rich Text</a>!]</em>'
            "</wagtail_block_caption>"
            "<strong>The following text is surrounded by strong tags.</strong>",
        )
