from wagtail import VERSION as WAGTAIL_VERSION

if WAGTAIL_VERSION >= (3, 0):
    from wagtail import blocks
else:
    from wagtail.core import blocks

from wagtail.images.blocks import ImageChooserBlock


class HeadingBlock(blocks.StructBlock):
    text = blocks.CharBlock(classname="title")
    importance = blocks.ChoiceBlock(
        choices=(
            ("h1", "H1"),
            ("h2", "H2"),
            ("h3", "H3"),
            ("h4", "H4"),
            ("h5", "H5"),
            ("h6", "H6"),
        ),
        default="h1",
    )

    class Meta:
        icon = "title"
        template = "wagtail_wordpress_import/heading_block.html"


class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    caption = blocks.CharBlock(required=False)
    link = blocks.URLBlock(required=False)
    alignment = blocks.ChoiceBlock(
        choices=(
            ("left", "Left"),
            ("right", "Right"),
            ("center", "Center"),
        ),
        default="left",
    )

    class Meta:
        icon = "image"
        template = "wagtail_wordpress_import/image_block.html"


class QuoteBlock(blocks.StructBlock):
    quote = blocks.CharBlock(form_classname="title")
    attribution = blocks.CharBlock(required=False)

    class Meta:
        icon = "openquote"
        template = "wagtail_wordpress_import/quote_block.html"


class WPImportStreamBlocks(blocks.StreamBlock):
    rich_text = blocks.RichTextBlock()
    heading = HeadingBlock()
    image = ImageBlock()
    block_quote = QuoteBlock()
    raw_html = blocks.RawHTMLBlock()
