import responses
from bs4 import BeautifulSoup
from django.test import TestCase
from wagtail.images import get_image_model

from wagtail_wordpress_import.prefilters.handle_shortcodes import (
    SHORTCODE_HANDLERS,
    BlockShortcodeHandler,
    CaptionHandler,
    register,
)
from wagtail_wordpress_import.test.tests.utility_functions import mock_image


class TestBlockShortcodeRegex(TestCase):
    def test_shortcode_is_found(self):
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = "foo"
            custom_html_tag_prefix = "wagtail_block_"

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
            custom_html_tag_prefix = "wagtail_block_"

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
            custom_html_tag_prefix = "wagtail_block_"

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
            custom_html_tag_prefix = "wagtail_block_"

        handler = FooHandler()
        html = "Metasyntactic variables [foo and the like] are common placeholders"

        match = handler._pattern.search(html)
        self.assertFalse(match)


class TestShortcodeAttrubuteValidation(TestCase):
    def test_shortcode_name_not_set(self):
        class FooHandler(BlockShortcodeHandler):
            pass

        with self.assertRaises(NotImplementedError) as ctx:
            FooHandler()
        self.assertEqual(
            "Create a subclass of BlockShortcodeHandler with a shortcode_name attribute",
            str(ctx.exception),
        )

    def test_shortcode_cannot_start_with_space(self):
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = " foo"

        with self.assertRaises(ValueError) as ctx:
            FooHandler()
        self.assertEqual(
            "The shortcode_name attribute must use upper or lower case letters or digits and cannot contain spaces",
            str(ctx.exception),
        )

    def test_shortcode_cannot_end_with_space(self):
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = "foo "

        with self.assertRaises(ValueError) as ctx:
            FooHandler()
        self.assertEqual(
            "The shortcode_name attribute must use upper or lower case letters or digits and cannot contain spaces",
            str(ctx.exception),
        )

    def test_shortcode_cannot_contain_spaces(self):
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = "fo o"

        with self.assertRaises(ValueError) as ctx:
            FooHandler()
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
            custom_html_tag_prefix = "wagtail_block_"

        html = "ham[foo]eggs[/foo]spam"
        handler = FooHandler()
        html = handler.pre_filter(html)
        self.assertEqual(html, "ham<wagtail_block_foo>eggs</wagtail_block_foo>spam")

    def test_shortcode_at_the_start_of_a_string(self):
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = "foo"
            custom_html_tag_prefix = "wagtail_block_"

        html = "[foo]radiators[/foo]jam"
        handler = FooHandler()
        html = handler.pre_filter(html)
        self.assertEqual(html, "<wagtail_block_foo>radiators</wagtail_block_foo>jam")

    def test_beautifulsoup_can_parse(self):
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = "foo"
            custom_html_tag_prefix = "wagtail_block_"

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
            custom_html_tag_prefix = "wagtail_block_"

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
            custom_html_tag_prefix = "wagtail_block_"

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
            custom_html_tag_prefix = "wagtail_block_"

        original = "Some pretext [caption this however you want] "
        handler = CaptionHandler()
        html = handler.pre_filter(original)
        self.assertEqual(html, original)

    def test_known_content(self):
        class CaptionHandler(BlockShortcodeHandler):
            shortcode_name = "caption"
            custom_html_tag_prefix = "wagtail_block_"

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


class TestAbsentShortcodeHandlers(TestCase):
    def test_included_shortcodes(self):
        # prime the SHORTCODE_HANDLERS
        # note this class has not been registered
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = "foo"
            custom_html_tag_prefix = "wagtail_block_"

        caption_handler_instance = SHORTCODE_HANDLERS[0]()

        self.assertIsInstance(caption_handler_instance, CaptionHandler)
        self.assertNotIsInstance(caption_handler_instance, FooHandler)
        self.assertEqual(len(SHORTCODE_HANDLERS), 1)


class TestIncludedShortcodeHandlers(TestCase):
    def test_included_shortcodes(self):
        # prime the SHORTCODE_HANDLERS
        # note this class has been registered
        @register()
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = "foo"
            custom_html_tag_prefix = "wagtail_block_"

        caption_handler_instance = SHORTCODE_HANDLERS[0]()
        foo_handler_instance = SHORTCODE_HANDLERS[1]()

        self.assertIsInstance(caption_handler_instance, CaptionHandler)
        self.assertIsInstance(foo_handler_instance, FooHandler)
        self.assertEqual(len(SHORTCODE_HANDLERS), 2)


class TestProvidedShortcodeIsTopLevel(TestCase):
    """
    Block Shortcode Handler has a is_top_level_html_tag property that is True by default.
    It can be set to False to indicate that the shortcode is not a top level HTML tag.
    """

    def test_is_top_level_html_tag_defaults_to_true(self):
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = "foo"

        foo = FooHandler()
        self.assertTrue(foo.is_top_level_html_tag)

    def test_is_top_level_html_tag_can_be_overridden(self):
        class FooHandler(BlockShortcodeHandler):
            shortcode_name = "foo"
            is_top_level_html_tag = False

        foo = FooHandler()
        self.assertFalse(foo.is_top_level_html_tag)


class TestShortcodeHandlerStreamfieldBlockCreation(TestCase):
    @responses.activate
    def test_construct_block_method_output(self):
        responses.add(
            responses.GET,
            "https://www.example.com/images/j-money-family-portrait.jpg",
            body=mock_image().read(),
            status=200,
            content_type="image/jpeg",
        )
        handler = CaptionHandler()
        wagtail_custom_html = BeautifulSoup(
            '<wagtail_block_caption id="46162" align="aligncenter" width="600">'
            '<img class="size-full" '
            'src="https://www.example.com/images/j-money-family-portrait.jpg" '
            'alt="This describes the image" width="600" height="338" /> '
            "<em>[This is a caption about the image (the one above) in "
            '<a href="https//www.example.com/bar/" target="_blank" '
            'rel="noopener noreferrer">Glorious Rich Text</a>!]</em>'
            "</wagtail_block_caption>",
            "html.parser",
        )
        json = handler.construct_block(
            wagtail_custom_html.find("wagtail_block_caption")
        )
        image = get_image_model().objects.get(title="j-money-family-portrait.jpg")

        self.assertIsInstance(json, dict)
        self.assertEqual(json["type"], "image")
        self.assertEqual(json["value"]["image"], image.id)
        self.assertEqual(
            json["value"]["caption"],
            "[This is a caption about the image (the one above) in Glorious Rich Text!]",
        )
        self.assertEqual(json["value"]["alignment"], "center")
        self.assertEqual(json["value"]["link"], "https//www.example.com/bar/")


class TestCaptionHandler(TestCase):
    @responses.activate
    def test_absence_of_image(self):
        handler = CaptionHandler()
        wagtail_custom_html = """
        <wagtail_block_caption id="attachment_46162" align="aligncenter" width="600">
            <a href="http://www.example.com/">

            </a>This is a caption about the image
        </wagtail_block_caption>"""

        output = handler.construct_block(
            BeautifulSoup(wagtail_custom_html, "html.parser").find(
                f"wagtail_block_{handler.shortcode_name}"
            )
        )
        # The image is not present in the html, the output should be a raw_html block
        self.assertEqual(output["type"], "raw_html")
        self.assertTrue("No image found in caption" in output["value"])

    @responses.activate
    def test_construct_block_method_output(self):
        handler = CaptionHandler()
        responses.add(
            responses.GET,
            "https://www.example.com/images/foo.jpg",
            body=mock_image().read(),
            status=200,
            content_type="image/jpeg",
        )
        wagtail_custom_html = """
        <wagtail_block_caption id="attachment_46162" align="aligncenter" width="600">
            <a href="http://www.example.com/">
                <img
                    class="wp-image-46162 size-full"
                    src="https://www.example.com/images/foo.jpg"
                    alt="This describes the image"
                    width="600"
                    height="338" />
            </a>This is a caption about the image
        </wagtail_block_caption>"""
        output = handler.construct_block(
            BeautifulSoup(wagtail_custom_html, "html.parser").find(
                f"wagtail_block_{handler.shortcode_name}"
            )
        )
        image = get_image_model().objects.get(title="foo.jpg")
        self.assertEqual(output["type"], "image")
        self.assertEqual(output["value"]["image"], image.id)
        self.assertEqual(
            output["value"]["caption"], "This is a caption about the image"
        )
        self.assertEqual(output["value"]["alignment"], "center")
        self.assertEqual(output["value"]["link"], "http://www.example.com/")

    @responses.activate
    def test_absence_of_alignment(self):
        handler = CaptionHandler()
        responses.add(
            responses.GET,
            "https://www.example.com/images/foo.jpg",
            body=mock_image().read(),
            status=200,
            content_type="image/jpeg",
        )
        wagtail_custom_html = """
        <wagtail_block_caption id="attachment_46162" width="600">
            <a href="http://www.example.com/">
                <img
                    class="wp-image-46162 size-full"
                    src="https://www.example.com/images/foo.jpg"
                    alt="This describes the image"
                    width="600"
                    height="338" />
            </a>This is a caption about the image
        </wagtail_block_caption>"""

        output = handler.construct_block(
            BeautifulSoup(wagtail_custom_html, "html.parser").find(
                f"wagtail_block_{handler.shortcode_name}"
            )
        )
        image = get_image_model().objects.get(title="foo.jpg")
        self.assertEqual(output["type"], "image")
        self.assertEqual(output["value"]["image"], image.id)
        self.assertEqual(
            output["value"]["caption"], "This is a caption about the image"
        )
        self.assertEqual(output["value"]["alignment"], "left")
        self.assertEqual(output["value"]["link"], "http://www.example.com/")

    @responses.activate
    def test_absence_of_an_anchor(self):
        handler = CaptionHandler()
        responses.add(
            responses.GET,
            "https://www.example.com/images/foo.jpg",
            body=mock_image().read(),
            status=200,
            content_type="image/jpeg",
        )
        wagtail_custom_html = """
        <wagtail_block_caption id="attachment_46162" align="aligncenter" width="600">
                <img
                    class="wp-image-46162 size-full"
                    src="https://www.example.com/images/foo.jpg"
                    alt="This describes the image"
                    width="600"
                    height="338" />
            This is a caption about the image
        </wagtail_block_caption>"""
        output = handler.construct_block(
            BeautifulSoup(wagtail_custom_html, "html.parser").find(
                f"wagtail_block_{handler.shortcode_name}"
            )
        )
        image = get_image_model().objects.get(title="foo.jpg")
        self.assertEqual(output["type"], "image")
        self.assertEqual(output["value"]["image"], image.id)
        self.assertEqual(
            output["value"]["caption"], "This is a caption about the image"
        )
        self.assertEqual(output["value"]["alignment"], "center")
        self.assertEqual(output["value"]["link"], "")
