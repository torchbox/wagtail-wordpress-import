import re

from wagtail_wordpress_import.block_builder_defaults import get_or_save_image

SHORTCODE_HANDLERS = []


def register():
    """Register the decorated class as a shortcode handler.

    Usage:

        from wagtail_wordpress_import.prefilters.handle_shortcodes import BlockShortcodeHandler, register

        @register("foo")
        class MyShortcodeHandler(BlockShortcodeHandler):
            shortcode_name = "foo"
    """

    def _wrapper(cls):
        SHORTCODE_HANDLERS.append(cls)
        return cls

    return _wrapper


class BlockShortcodeHandler:

    shortcode_name: str

    is_top_level_html_tag = True

    def __init__(self):
        # Subclasses should declare a shortcode_name
        if not hasattr(self, "shortcode_name"):
            raise NotImplementedError(
                "Create a subclass of BlockShortcodeHandler with a shortcode_name attribute"
            )
        pattern = re.compile(r"^\S[a-zA-Z0-9_\S]+\S$")
        # shortcode_name must use upper or lower case letters or digits and cannot contain spaces
        if not re.match(pattern, self.shortcode_name):
            raise ValueError(
                "The shortcode_name attribute must use upper or lower case letters or digits and cannot contain spaces"
            )

    @property
    def _pattern(self):
        """Return a regex to match a block shortcode and capture the attrs and text.

        Given an input:

            "Preface [foo bar=1]some text[/foo] epilogue."

        the regex will match the string between the two "foo" tags, inclusively. The
        capture group "attrs" will match " bar=1", and capture group "content" will
        match "some text".
        """

        return re.compile(
            r"\["  # matches the opening [
            + self.shortcode_name
            + r"\b"  # matches a word boundary
            + r"(?P<attrs>[^\]]*)"  # capture 'attrs', matching anything but ]
            + r"\]"  # matches the closing ] of the opening tag
            + r"(?P<content>.*?)"  # non-greedily captures 'content' between the tags
            + r"\[\/"  # matches the  [/ of the closing tag
            + self.shortcode_name
            + r"\]"  # matches the closing ]
        )

    def pre_filter(self, string):
        """Replace all occurrences of the tag with a HTML tag for later parsing.

        Given an input:

            "Preface [foo bar=1]some text[/foo] epilogue."

        this function will return

            "Preface <wagtail_block_foo bar=1>some text</wagtail_block_foo> epilogue."
        """
        string, matches = self._pattern.subn(
            r"<"
            + self.element_name
            + r"\g<attrs>>\g<content></"
            + self.element_name
            + r">",
            string,
        )

        return string

    @property
    def element_name(self):
        return f"wagtail_block_{self.shortcode_name}"


# Subclasses should declare a shortcode_name and provide
# a construct_block method for converting the pre-filtered HTML to a
# Wagtail StreamField block dict.
@register()
class CaptionHandler(BlockShortcodeHandler):
    """
    The Wordpress caption tag is replaced by the custom HTML tag. The caption content and caption attrubutes
    are preserved and included in the custom HTML tag.

    Sample wordpress caption tag:

    [caption id="attachment_46162" align="aligncenter" width="600"]
    <a href="http://www.example.com/">
    <img class="wp-image-46162 size-full" src="https://www.example.com/images/foo.jpg" alt="This describes the image" width="600" height="338" />
    </a>
    This is a caption about the image[/caption]

    is replaced by:

    <wagtail_block_caption id="attachment_46162" align="aligncenter" width="600">
    <a href="http://www.example.com/">
    <img class="wp-image-46162 size-full" src="https://www.example.com/images/foo.jpg" alt="This describes the image" width="600" height="338" />
    </a>
    This is a caption about the image</wagtail_block_caption>

    in the pre-filter method on the parent BlockShortcodeHandler class.
    """

    shortcode_name = "caption"

    def construct_block(self, soup):
        """Construct a StreamBlock dict that's passed back to the block builder

        soup: <class 'bs4.element.Tag'>
        """

        # Without an image the caption shortcode is useless
        # Here we'll add a raw HTML block to the stream so in admin
        # it can be seen and some action taken.
        image = soup.find("img")
        if not image:
            return {
                "type": "raw_html",
                "value": f"<!-- No image found in caption {soup}-->",
            }
        # TODO: Output this in logging when we have a logger
        # https://projects.torchbox.com/projects/wordpress-to-wagtail-importer-package/tickets/63

        # Parse the image
        image_file = get_or_save_image(image.attrs["src"])

        # Parse alignment
        if "align" in soup.attrs:
            alignment = soup.attrs["align"].replace("align", "")
        else:
            alignment = "left"

        # Parse the caption
        caption = soup.text.replace("\n", "").strip()

        # Parse the anchor link
        # The template has a conditional that only render the link
        # if the return value["link"] has a value
        anchor = soup.find("a")
        if anchor:
            link = anchor.attrs["href"]
        else:
            link = ""

        return {
            "type": "image",
            "value": {
                "image": image_file.id,
                "caption": caption,
                "alignment": alignment,
                "link": link,
            },
        }


def filter_transform_shortcodes(html, options=None):
    """
    html: is the body content from one Wordpress item
    options: not implemented
    """
    for handler in SHORTCODE_HANDLERS:
        html = handler().pre_filter(html)
    return html
