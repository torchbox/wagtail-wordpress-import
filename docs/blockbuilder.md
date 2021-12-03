# Block Builder

- [Block Builder](#block-builder)
  - [What is a Block Builder?](#what-is-a-block-builder)
  - [How does the Block Builder work?](#how-does-the-block-builder-work)
  - [Included Blocks](#included-blocks)
    - [Heading Block `<h1>`](#heading-block-h1)
    - [Table Block `<table>`](#table-block-table)
    - [Iframe Block `<iframe>`](#iframe-block-iframe)
    - [Form Block `<form>`](#form-block-form)
    - [Image Block `<img />`](#image-block-img-)
    - [Blockquote Block `<blockquote>`](#blockquote-block-blockquote)
    - [Included Fallback Block](#included-fallback-block)
  - [Configuration](#configuration)
    - [Examples](#examples)
      - [Headings as separate blocks](#headings-as-separate-blocks)
      - [Custom blockquote](#custom-blockquote)
  - [Extending the package WPImportStreamBlocks](#extending-the-package-wpimportstreamblocks)

## What is a Block Builder?

The Block Builder transforms the body HTML content which could contain a lot of HTML tags and content into a sequence of Wagtail StreamField blocks.

It does this by parsing the HTML content and converting each top level tag it finds into a specific block type defined in settings.

The default StreamBlock mapping:

```python
WAGTAIL_WORDPRESS_IMPORTER_CONVERT_HTML_TAGS_TO_BLOCKS = {
    "h1": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
    "table": "wagtail_wordpress_import.block_builder_defaults.build_table_block",
    "iframe": "wagtail_wordpress_import.block_builder_defaults.build_iframe_block",
    "form": "wagtail_wordpress_import.block_builder_defaults.build_form_block",
    "img": "wagtail_wordpress_import.block_builder_defaults.build_image_block",
    "blockquote": "wagtail_wordpress_import.block_builder_defaults.build_block_quote_block",
}
```

Any HTML tags encountered during parsing that don't have a mapping in the settings above are combined into a single fallback StreamField block. This generally means that consecutive `<p>` tags are combined into the same block.

It's possible other HTML tags that are not included in the default mapping will also be combined into the RichTextBlock. This may not be the desired behaviour for your data. To import HTML tags that are not in the default mapping, or to change the default behaviour for a specific HTML tag, you can change the mapping in your own site's settings.

The default fallback block builder function returns a RichTextBlock. You can override this in settings:

```python
WAGTAIL_WORDPRESS_IMPORTER_FALLBACK_BLOCK = "my_fallback_block_builder_function"
```

## How does the Block Builder work?

After all the HTML content has been parsed and converted into a sequence of StreamField blocks it is held in memory as a dict and then saved to the Wagtail page instance StreamField.

While creating each StreamField block the Block Builder will also implement the following:

1. Find images in the HTML content and download them to the Wagtail images app and link them correctly using the image ID.
2. Find linked documents in the HTML content and download them to the Wagtail documents app and link them correctly using the document ID.

Internally the Block Builder uses the `BeautifulSoup` package to parse the HTML content.

---

## Included Blocks

### Heading Block `<h1>`

Builder function:

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

### Table Block `<table>`

Filter:

```python
def build_table_block(tag):
    block_dict = {"type": "raw_html", "value": str(tag)}
    return block_dict
```

Wagtail Block:

```python
blocks.RawHTMLBlock()
```

### Iframe Block `<iframe>`

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

### Form Block `<form>`

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

### Image Block `<img />`

*This block is not being used at the moment and is likely to be removed or repurposed in future versions.*

Filter:

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

### Blockquote Block `<blockquote>`

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

### Included Fallback Block

By default, the fallback block is a Wagtail `RichText` Block.

Only content that has no specific block filter is added to the fallback block.

Example: `<p> <ul> <a> <img /> ...`

*This block is only saved to the block sequence each time the builder determines that a new Block is required in the sequence or the builder has reached the end of the content parsing.*

This block has extra processing included each time it is saved as a block to the block sequence.

1. The `<img />` src values are parsed. The `<img />` tags are updated to the Wagtail RichText embedded content type. e.g. `<embed embedtype="image" id="1001" alt="A image description" format="left" />`
2. The `<a href="..."></a>` href values are parsed for document links. The document links are are updated to the Wagtail RichText linktype format. e.g. `<a id="1001" linktype="document">link</a>`

Linking of Images and Documents will only happen if the they are part of the same domain as the imported site. They are downloaded and saved to the Wagtail Images or Documents app.

Note: The fallback block may contain other HTML `<a>` tags that are links to other pages in your Wagtail site. These links are not processed by the block builder but are processed at the end of the import process because all the imported pages need to exist for this to happen.

Filter:

```python
def build_richtext_block_content(cache, blocks):
    # image_linker is called to link up and retrieve the remote images
    cache = image_linker(cache)
    # document_linker is called to link up and retrieve the remote documents
    cache = document_linker(cache)
    blocks.append({"type": "rich_text", "value": cache})
    cache = ""
    return cache
```

Wagtail Block

```python
# the features of a RichText block are customised from the Wagtail default

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
```

---

## Configuration

You can add your own configuration to control the Block Building process.

Below is the included configuration.

```python
WAGTAIL_WORDPRESS_IMPORTER_CONVERT_HTML_TAGS_TO_BLOCKS = {
    "h1": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
    "table": "wagtail_wordpress_import.block_builder_defaults.build_table_block",
    "iframe": "wagtail_wordpress_import.block_builder_defaults.build_iframe_block",
    "form": "wagtail_wordpress_import.block_builder_defaults.build_form_block",
    "img": "wagtail_wordpress_import.block_builder_defaults.build_image_block",
    "blockquote": "wagtail_wordpress_import.block_builder_defaults.build_block_quote_block",
}
```

### Examples

#### Headings as separate blocks

Include the `h1` - `h6` HTML tags in the config to create them as separate StreamField blocks for each heading size.

Copy the default configuration below to your own site's settings and add the required HTML tags with an corresponding function to be called for each tag.

```python
WAGTAIL_WORDPRESS_IMPORTER_CONVERT_HTML_TAGS_TO_BLOCKS = {
    "h1": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
    "h2": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
    "h3": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
    "h4": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
    "h5": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
    "h6": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
    "table": "wagtail_wordpress_import.block_builder_defaults.build_table_block",
    "iframe": "wagtail_wordpress_import.block_builder_defaults.build_iframe_block",
    "form": "wagtail_wordpress_import.block_builder_defaults.build_form_block",
    "img": "wagtail_wordpress_import.block_builder_defaults.build_image_block",
    "blockquote": "wagtail_wordpress_import.block_builder_defaults.build_block_quote_block",
}
```

*The package provided block builder function for headings will work as expected for this example therefore a new Block Builder function isn't required.*

#### Custom blockquote

Change the Block Builder function to use your own provided function to create a `blockquote` block.

Copy the default configuration below to your own sites settings and add the required function to build the block.

```python
WAGTAIL_WORDPRESS_IMPORTER_CONVERT_HTML_TAGS_TO_BLOCKS = {
    "h1": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
    "table": "wagtail_wordpress_import.block_builder_defaults.build_table_block",
    "iframe": "wagtail_wordpress_import.block_builder_defaults.build_iframe_block",
    "form": "wagtail_wordpress_import.block_builder_defaults.build_form_block",
    "img": "wagtail_wordpress_import.block_builder_defaults.build_image_block",
    "blockquote": "path.to.my_site.block.functions.my_block_quote",
}
```

and create a filter function in your own Wagtail site which will receive a single parameter for the tag. The tag is a `BeautifulSoup` tag object.

```python
def my_block_quote(tag):
    """Return a Python dict with the block type and value.
    
    The value could contain child blocks, depending on your implementation.
    """
    return {
        "type": "block_quote_block",  # the StreamField block type name
        "value": {
            "quote": tag.text.strip(), 
            "attribution": tag.cite,
        }
    }
```

In your own site you could have a block class like the example below

Wagtail Block:

```python
class MyQuoteBlock(blocks.StructBlock):
    quote = blocks.CharBlock()
    attribution = blocks.CharBlock(required=False)

    class Meta:
        # choose the icon thats most appropriate here
        icon = "openquote" 
        # and also define a template for the block
        template = "templates/blocks/my_quote_block.html"
```

In your own sites StreamField block the block type will need to be available with the name `block_quote_block` for this example but you can call your block type whatever you want.

```python
# your Wagtail page model
class MyPage(Page):
    body = StreamField(MyStreamBlocks(), required=False)
    ...

    content_panels = Page.content_panels + [
        StreamFieldPanel("body")
    ]
    ...

# your Wagtail stream block class
class MyStreamBlocks(blocks.StreamBlock):
    block_quote_block = MyQuoteBlock()
    ...
```

The [Wagtail Docs](https://docs.wagtail.io/en/stable/topics/streamfield.html) have a full example of creating custom blocks and block types.

---

## Extending the package WPImportStreamBlocks

While you can you can extend the package provided WPImportStreamBlocks we recommend you use your own custom block types and StreamFields / StreamBlocks. This is because the package is not meant to be used in your own site after the import process has been completed. Once it's removed the package blocks and block types will not be available.

You should create your own custom block types and use them in your own Wagtail page model StreamFields.

The recommended approach is to copy the package defaults to your own Wagtail site from: `wagtail_wordpress_import/blocks.py` and adjust them to your own needs.

Also copy `wagtail_wordpress_import/block_builder_defaults.py` and create your own functions for each block type you want to use.

Then add your own `WAGTAIL_WORDPRESS_IMPORTER_CONVERT_HTML_TAGS_TO_BLOCKS` to your own setting and map the HTML tags to the functions you created.
