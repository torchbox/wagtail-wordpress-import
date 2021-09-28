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
        template = "wagtail_xmlimport/heading_block.html"


class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    caption = blocks.CharBlock(required=False)

    class Meta:
        icon = "image"
        template = "wagtail_xmlimport/image_block.html"


class QuoteBlock(blocks.StructBlock):
    quote = blocks.CharBlock(form_classname="title")
    attribution = blocks.CharBlock(required=False)

    class Meta:
        icon = "openquote"
        template = "wagtail_xmlimport/quote_block.html"


class WPImportStreamBlocks(blocks.StreamBlock):
    rich_text = blocks.RichTextBlock(
        features=[
            "anchor-identifier",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "bold",
            "italic",
            "ol",
            "ul",
            "hr",
            "link",
            "document-link",
            "image",
            "embed",
            "superscript",
            "subscript",
            "strikethrough",
            "blockquote",
        ]
    )
    heading = HeadingBlock()
    image = ImageBlock()
    block_quote = QuoteBlock()
    raw_html = blocks.RawHTMLBlock()
