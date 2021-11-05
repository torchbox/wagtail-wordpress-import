from bs4 import BeautifulSoup
from django.test import TestCase

from wagtail_wordpress_import.prefilters.handle_shortcodes import (
    SHORTCODE_HANDLERS,
    BlockShortcodeHandler,
    CaptionHandler,
    register,
)


class TestBlockShortcodeRegex(TestCase):
    def test_shortcode_is_found(self):
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = "foo"

        handler = FooHandler()
        html = "foo[foo]baz[/foo]quux"

        match = handler._pattern.search(html)
        self.assertEqual(match.start(), 3)
        self.assertEqual(match.end(), 17)
        self.assertEqual(match.group("content"), "baz")
        self.assertEqual(match.group("attrs"), "")

    def test_multiple_shortcodes_are_found(self):
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = "foo"

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
            shortcode_name = "foo"

        handler = FooHandler()
        html = "embalmed ones[foo][stray dogs][/foo]"

        match = handler._pattern.search(html)

        self.assertEqual(match.start(), 13)
        self.assertEqual(match.end(), 36)
        self.assertEqual(
            match.group("content"),
            "[stray dogs]",
        )
        self.assertEqual(match.group("attrs"), "")

    def test_block_shortcode_handler_requires_the_closing_shortcode_tag(self):
        """This tests that an aside in square brackets is not accidentally matched."""

        class FooHandler(BlockShortcodeHandler):
            shortcode_name = "foo"

        handler = FooHandler()
        html = "Metasyntactic variables [foo and the like] are common placeholders"

        match = handler._pattern.search(html)
        self.assertFalse(match)


class TestShortcodeAttrubuteValidation(TestCase):
    def test_shortcode_name_not_set(self):
        class FooHandler(BlockShortcodeHandler):
            pass

        with self.assertRaises(NotImplementedError) as ctx:
            handler = FooHandler()
        self.assertEqual(
            "Create a subclass of BlockShortcodeHandler with a shortcode_name attribute",
            str(ctx.exception),
        )

    def test_shortcode_cannot_start_with_space(self):
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = " foo"

        with self.assertRaises(ValueError) as ctx:
            handler = FooHandler()
        self.assertEqual(
            "The shortcode_name attribute must use upper or lower case letters or digits and cannot contain spaces",
            str(ctx.exception),
        )

    def test_shortcode_cannot_end_with_space(self):
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = "foo "

        with self.assertRaises(ValueError) as ctx:
            handler = FooHandler()
        self.assertEqual(
            "The shortcode_name attribute must use upper or lower case letters or digits and cannot contain spaces",
            str(ctx.exception),
        )

    def test_shortcode_cannot_contain_spaces(self):
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = "fo o"

        with self.assertRaises(ValueError) as ctx:
            handler = FooHandler()
        self.assertEqual(
            "The shortcode_name attribute must use upper or lower case letters or digits and cannot contain spaces",
            str(ctx.exception),
        )


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
            shortcode_name = "foo"

        html = "ham[foo]eggs[/foo]spam"
        handler = FooHandler()
        html = handler.pre_filter(html)
        self.assertEqual(html, "ham<wagtail_block_foo>eggs</wagtail_block_foo>spam")

    def test_shortcode_at_the_start_of_a_string(self):
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = "foo"

        html = "[foo]radiators[/foo]jam"
        handler = FooHandler()
        html = handler.pre_filter(html)
        self.assertEqual(html, "<wagtail_block_foo>radiators</wagtail_block_foo>jam")

    def test_beautifulsoup_can_parse(self):
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = "foo"

        html = "ham[foo]eggs[/foo]spam"
        handler = FooHandler()
        html = handler.pre_filter(html)
        soup = BeautifulSoup(html, "html.parser")
        tags = soup.find_all(True)
        self.assertEqual(len(tags), 1)
        self.assertEqual(str(tags[0]), "<wagtail_block_foo>eggs</wagtail_block_foo>")

    def test_beautifulsoup_can_parse_attrs(self):
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = "foo"

        html = 'ham[foo quantity=3 state="over easy" garnish="more spam"]eggs[/foo]spam'
        handler = FooHandler()
        html = handler.pre_filter(html)
        soup = BeautifulSoup(html, "html.parser")
        tags = soup.find_all(True)
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0]["quantity"], "3")
        self.assertEqual(tags[0]["state"], "over easy")
        self.assertEqual(tags[0]["garnish"], "more spam")

    def test_caption(self):
        class CaptionHandler(BlockShortcodeHandler):
            shortcode_name = "caption"

        html = 'Some pretext[caption width="100"]The content of the tag[/caption]'
        handler = CaptionHandler()
        html = handler.pre_filter(html)
        self.assertEqual(
            html,
            'Some pretext<wagtail_block_caption width="100">The content of the tag</wagtail_block_caption>',
        )

    def test_unclosed_shortcode_rejected_by_block_shortcode_handler(self):
        """This tests that an aside in square brackets is not accidentally matched."""

        class CaptionHandler(BlockShortcodeHandler):
            shortcode_name = "caption"

        original = "Some pretext [caption this however you want] "
        handler = CaptionHandler()
        html = handler.pre_filter(original)
        self.assertEqual(html, original)

    def test_known_content(self):
        class CaptionHandler(BlockShortcodeHandler):
            shortcode_name = "caption"

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


class TestShortcodeHandlerRegistration(TestCase):
    def test_developer_provided_shortcode_handlers_are_registered(self):
        @register("foo")
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = "foo"

        registered_handlers = SHORTCODE_HANDLERS.keys()
        self.assertIn("foo", registered_handlers)
        self.assertIn("caption", registered_handlers)


class TestShortcodeHandlerStreamfieldBlockCreation(TestCase):
    def test_construct_block_method_output(self):
        handler = CaptionHandler()
        wagtail_custom_html = (
            '<wagtail_block_caption id="attachment_46162" align="aligncenter" width="600">'
            '<img class="wp-image-46162 size-full" '
            'src="https://www.example.com/images/foo.jpg" '
            'alt="This describes the image" width="600" height="338" /> '
            "<em>[This is a caption about the image (the one above) in "
            '<a href="https//www.example.com/bar/" target="_blank" '
            'rel="noopener noreferrer">Glorious Rich Text</a>!]</em>'
            "</wagtail_block_caption>"
        )
        json = handler.construct_block(wagtail_custom_html)
        self.assertDictEqual(
            json,
            {
                "type": "image_block",
                "value": {
                    "image_file": 1,
                    "tag_attrs": {
                        "id": "attachment_46162",
                        "align": "aligncenter",
                        "width": "600",
                    },
                    "image_attrs": {
                        "class": ["wp-image-46162", "size-full"],
                        "src": "https://www.example.com/images/foo.jpg",
                        "alt": "This describes the image",
                        "width": "600",
                        "height": "338",
                    },
                    "anchor_attrs": {
                        "href": "https//www.example.com/bar/",
                        "target": "_blank",
                        "rel": ["noopener", "noreferrer"],
                    },
                },
            },
        )
