# Block Builder

- [Block Builder](#block-builder)
  - [Included Blocks](#included-blocks)
      - [Heading Block `<h1>, <h2>, <h3>, <h4>, <h5>, <h6>`](#heading-block-h1-h2-h3-h4-h5-h6)
      - [Table Block `<table>`](#table-block-table)
      - [Iframe Block `<iframe>`](#iframe-block-iframe)
      - [Form Block `<form>`](#form-block-form)
      - [Image Block `<img />` `TODO not yet complete, likely to come from shortcode parsing`](#image-block-img--todo-not-yet-complete-likely-to-come-from-shortcode-parsing)
      - [Blockquote Block `<blockquote>`](#blockquote-block-blockquote)
  - [Included Fallback/Catch-all Block](#included-fallbackcatch-all-block)
  - [Configuration](#configuration)

The block builder takes the page body content in as a string of HTML.
The filters listed below are then used to parse the HTML into a sequence of StreamField blocks.

The parsing process uses Beautiful Soup to analyze each top level HTML tag in the order they appear in the HTML body content. If a match is found in the `WAGTAIL_WORDPRESS_IMPORTER_CONVERT_HTML_TAGS_TO_BLOCKS` configuration a single block is created for the HTML tag.

---

## Included Blocks

#### Heading Block `<h1>, <h2>, <h3>, <h4>, <h5>, <h6>` 

Builder:

```python
def build_heading_block(tag):
    block_dict = {
        "type": "heading",
        "value": {"importance": tag.name, "text": tag.text},
    }
    return block_dict
```

Wagtail Block:

```python
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
```

#### Table Block `<table>`
Filter: 
```python
def build_table_block(tag):
    block_dict = {"type": "raw_html", "value": str(tag)}
    return block_dict
```
Wagtail Block:
```
blocks.RawHTMLBlock()
```

#### Iframe Block `<iframe>`
Filter: 
```python
def build_iframe_block(tag):
    block_dict = {
        "type": "raw_html",
        "value": '<div class="core-custom"><div class="responsive-iframe">{}</div></div>'.format(
            str(tag)
        ),
    }
    return block_dict
```
Wagtail Block:
```python
blocks.RawHTMLBlock()
```

#### Form Block `<form>`
Filter: 
```python
def build_form_block(tag):
    block_dict = {"type": "raw_html", "value": str(tag)}
    return block_dict
```
Wagtail Block:
```python
blocks.RawHTMLBlock()
```

#### Image Block `<img />` `TODO not yet complete, likely to come from shortcode parsing`

Filter: `TODO not yet complete
```python
def build_image_block(tag):
    def get_image_id(src):
        return 1

    block_dict = {"type": "image", "value": get_image_id(tag.src)}
    return block_dict
```
Wagtail Block
```python
class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    caption = blocks.CharBlock(required=False)

    class Meta:
        icon = "image"
        template = "wagtail_wordpress_import/image_block.html"
```

#### Blockquote Block `<blockquote>`
Filter:
```python
def build_block_quote_block(tag):
    block_dict = {
        "type": "block_quote",
        "value": {"quote": tag.text.strip(), "attribution": tag.cite},
    }
    return block_dict
```
Wagtail Block:
```python
class QuoteBlock(blocks.StructBlock):
    quote = blocks.CharBlock(form_classname="title")
    attribution = blocks.CharBlock(required=False)

    class Meta:
        icon = "openquote"
        template = "wagtail_wordpress_import/quote_block.html"
```

## Included Fallback/Catch-all Block

By default, the fallback block is a Wagtail `RichText` Block.

Only content that has no specific block filter is added to the fall back block.

Example: `<p> <ul> <a> <img /> ...`

This block is only saved to the block sequence each time the builder finds a new Block is required or the builder has reached the end of the content parsing.

This block has extra processing included each time it is saved as a block to the block sequence.

1. All the `<img />` src values are analyzed and if the image is a local to site image it is fetched and saved to the Wagtail Images app. The `<img />` tags are updated to the Wagtail rich text embedded content type. e.g. `<embed embedtype="image" id="1001" alt="A image description" format="left" />`
2. All the `<a href="..."></a>` href values are analyzed and if the href is a document type it is fetched and saved to the Wagtail Documents app. The `<a href=""></a>` are updated to the Wagtail RichText linktype format. e.g. `<a id="1001" linktype="document">link</a>`

Filter:

```python
def build_none_block_content(cache, blocks):
    """
    image_linker is called to link up and retrive the remote image
    """
    cache = image_linker(cache)
    cache = document_linker(cache)
    blocks.append({"type": "rich_text", "value": cache})
    cache = ""
    return cache
```
Wagtail Block

```python
rich_text = blocks.RichTextBlock(
    # "h1","h2","h3","h4","h5","h6","image","embed",
    # are included to allow editing the content via the admin once the import is complete
    #they are used while the body content is parsed into blocks.
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
```

---

## Configuration

You can add your own configuration to control the Block Building process.

Below is the included configuration. You can copy this to your own settings and either add or remove tag to block filters.

```python
WAGTAIL_WORDPRESS_IMPORTER_CONVERT_HTML_TAGS_TO_BLOCKS = 
    [
        (
            "h1",{
                "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",},),
        (
            "h2",{
                "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",},),
        (
            "h3",{
                "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",},),
        (
            "h4",{
                "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",},),
        (
            "h5",{
                "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",},),
        (
            "h6",{
                "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",},),
        (
            "table",{
                "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_table_block",},),
        (
            "iframe",{
                "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_iframe_block",},),
        (
            "form",{
                "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_form_block",},),
        (
            "img",{
                "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_image_block",},),
        (
            "blockquote",{
                "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_block_quote_bloc",},),
    ]
```
Examples:

1. Include the `h1-h6` HTML tags in the fall back block and not have their own block types. Just remove the `h1-h6` filter configuration items in your own settings.
2. Add extra HTML tag processing: you would add a function somewhere in your own Wagtail app. Then add an item to the config above with the HTML tag key along with a `FUNCTION` which is the dotted path to the function you have created. You may also need to include the Wagtail Block in your own app or you could repurpose one of the provided Block types.
