# Converting Wordpress block shortcodes to StreamField blocks

- [Converting Wordpress block shortcodes to StreamField blocks](#converting-wordpress-block-shortcodes-to-streamfield-blocks)
  - [Block Shortcode handler class](#block-shortcode-handler-class)
  - [Caption shortcode handler (included)](#caption-shortcode-handler-included)
    - [CaptionHandler Pre-filter](#captionhandler-pre-filter)
    - [Caption StreamField block constructor](#caption-streamfield-block-constructor)
  - [How to create your own shortcode handlers](#how-to-create-your-own-shortcode-handlers)

## Block Shortcode handler class

The package is able to parse WordPress block shortcodes.

We provide a base class [BlockShortcodeHandler](/wagtail_wordpress_import/prefilters/handle_shortcodes.py#L27) that performs the transformation of the raw shortcode into a custom HTML tag using a regular expression.

The custom HTML tag will retain all the parts of the original shortcode which you can use to create the StreamField block.

The package includes a handler for the Wordpress `caption` shortcode called `CaptionHandler`. The handler pre-filter will transform the shortcode into a custom HTML tag. The `construct_block` method will transform the custom HTML tag to a dict representing the StreamField block. Shortcode handlers need to be registered using the provided  `@register` decorator.

---

## Caption shortcode handler (included)

[View CaptionHandler Source](/wagtail_wordpress_import/prefilters/handle_shortcodes.py#L102)

### CaptionHandler Pre-filter

The `BlockShortcodeHandler` uses a regular expression to parse the body content for shortcodes. If a match is found for a registered shortcode the `pre_filter` method will transform and replace the matched content into a custom HTML tag.

**For example:**

The Wordpress caption shortcode could look like the example below and be represented in the body content with the start text of `[caption ...]` and end text of `[/caption]`

A complete shortcode example:

```html
[caption id="attachment_46162" align="aligncenter" width="600"] <img class="wp-image-46162 size-full"  src="https://www.example.com/images/foo.jpg" alt="This describes the image" width="600" height="338" /><em>This is a caption about the image (the one above) in <a href="https//www.example.com/bar/" target="_blank" rel="noopener noreferrer">Glorious Rich Text</a>!</em>[/caption]
```

would be transformed and replaced with:

```html
<wagtail_block_caption id="attachment_46162" align="aligncenter" width="600"><img class="wp-image-46162 size-full" src="https://www.example.com/images/foo.jpg" alt="This describes the image" width="600" height="338" /><em>This is a caption about the image (the one above) in <a href="https//www.example.com/bar/" target="_blank" rel="noopener noreferrer">Glorious Rich Text</a>!</em></wagtail_block_caption>
```

*This transformation will happen at the pre-filter stage of the import process, so at this point the body content will have the whole shortcode replaced with the custom HTML. Later at the block builder stage, the custom HTML tag will be converted to a StreamField block.*

### Caption StreamField block constructor

The StreamField block dict is created from the custom HTML tag at the block builder stage. The [construct_block()](/wagtail_wordpress_import/prefilters/handle_shortcodes.py#L133) method of the CaptionHandler() class is passed the custom HTML tag by the block builder for parsing and will return a dict for the StreamField block.

*The StreamField block name used in the dict will need a matching Wagtail block type in your app. We provide an ImageBlock for the Caption shortcode handler.*

## How to create your own shortcode handlers

You will need to create a class that inherits from the provided `BlockShortcodeHandler` [source](/wagtail_wordpress_import/prefilters/handle_shortcodes.py)

A complete shortcode example:

```html
[card] <img src="https://www.example.com/images/foo.jpg" />Card title[/caption]
```

**PART 1** Create a class that inherits from BlockShortcodeHandler()

Import the BlockShortcodeHandler.

```python
from wagtail_wordpress_import.prefilters.handle_shortcodes import BlockShortcodeHandler
```

Create you shortcode handler class.

```python
class CardShortcodeHandler(BlockShortcodeHandler):
  shortcode_name = "card"
```

The card custom HTML tag:

```html
<wagtail_block_card><img class="wp-image-46162 size-full" src="https://www.example.com/images/foo.jpg" />Card title</wagtail_block_card>
```

Your class should declare a class attribute of `shortcode_name` (str) with a value of the Wordpress shortcode name you need to transform. In the example class above the custom HTML tag name will be `wagtail_block_card`.

*The shortcode_name will need to match the Wordpress shortcode, but it cannot contain spaces or special characters. The tag is never displayed in a browser directly.*

You will need to use a `@register` method provided to decorate your class so it will be added to the list of shortcode handlers to be run during the import process.

Import the register decorator:

```python
from wagtail_wordpress_import.prefilters.handle_shortcodes import register
```

Decorate your class:

```python
@register()
class CardShortcodeHandler(BlockShortcodeHandler):
  shortcode_name = "card"
```

In this card example your class will then transform the Wordpress shortcode to a custom HTML tag with the name `wagtail_block_card` during the import process.

**Part 2** Your class needs to create the StreamField dict which is used to build the StreamField block during the import process.

Add a method to your class called `construct_block` which takes one parameter. The parameter received will be a BeautifulSoup tag class, representing the `wagtail_block_card`.

A basic example:

```python
def construct_block(self, soup):
  """Assuming the card has a `title` and `image` for its HTML content
  As the `soup` parameter is a BeautifulSoup tag object you can use its methods to extract the data you need.
  """

  # parse the title
  try:
      title = soup.text.replace("\n", "").strip()
  except (KeyError, AttributeError, TypeError):
      title = ""

  # parse the image
  try:
      # get_or_save_image() is not included in the shortcode handler
      # it is included in the package and can be used if required
      # [source](wagtail_wordpress_import/block_builder_defaults.py#L222)
      image = soup.find("img")
      image_file = get_or_save_image(image.attrs["src"])
      image_id = image_file.id
  except (KeyError, AttributeError, TypeError):
      image_id = None

  # You can only return a single block type here but your block could contain child blocks.
  return {
      "type": "card_block",
      "value": {
        "title": title,
        "image": image_id 
      },
  }
```

**Part 3** The `type` of block in the dict you return will need a block and block template defined in your app and be available on the page model you are importing to.

For this example:

```python
class CardBlock(blocks.StructBlock):
  """The Wagtail block required for the card shortcode handler"""

  title = blocks.CharBlock(required=False)
  image_file = ImageChooserBlock()

  class Meta:
    # in this example the card block will need a template
    template = "path/to/block/templates/card_block.html"
```

The template could be:

```html
{% load wagtailimages_tags %}

<div class="card">
  {% if value.title %}
  <div class="card card-title">{{ value.title }}</div>
  {% endif %}
  <div class="card card-image">{% image value.image width-800 %}</div>
</div>
```

And your StreamField on your page model would need to include the CardBlock, see [How to use StreamField for mixed content](https://docs.wagtail.io/en/stable/topics/streamfield.html#how-to-use-streamfield-for-mixed-content) from the official Wagtail Documentation.
