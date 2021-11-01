# Wordpress shortcodes block converter

- [Wordpress shortcodes block converter](#wordpress-shortcodes-block-converter)
  - [Shortcode classes](#shortcode-classes)
  - [Included shortcode handlers](#included-shortcode-handlers)
    - [Caption shortcode](#caption-shortcode)
    - [Pre-filter example](#pre-filter-example)
    - [Block Creator example](#block-creator-example)
  - [Creating you own shortcode handlers](#creating-you-own-shortcode-handlers)
    - [TODO: I will need to expand more here about the json return value. We will also need to follow through with the example of faqlist I think. I'll have a clearer picture of whats required after the next couple of tickets are complete](#todo-i-will-need-to-expand-more-here-about-the-json-return-value-we-will-also-need-to-follow-through-with-the-example-of-faqlist-i-think-ill-have-a-clearer-picture-of-whats-required-after-the-next-couple-of-tickets-are-complete)

## Shortcode classes

The package is able to parse Wordpress shortcodes.

We provide a base class `BlockShortcodeHandler` that performs the transformation of the raw shortcode into a custom HTML tag using regular expressions.

The custom HTML tag will retain all the parts of the original shortcode which you can make use of when creating the StreamBlock json.

---

## Included shortcode handlers

### Caption shortcode

The package includes a shortcode handler for Wordpress `caption` shortcodes. The handler pre-filter will transform the shortcode into a custom HTML tag.

The transformation happens in the pre-filter method of the CaptionHandler class.

### Pre-filter example

Wordpress shortcode

```html
[caption id="attachment_46162" align="aligncenter" width="600"]
<img class="wp-image-46162 size-full" src="https://www.example.com/images/foo.jpg" alt="This describes the image" width="600" height="338" />
This is a caption about the image[/caption]
```

will be transformed to

```html
<wagtail_block_caption id="attachment_46162" align="aligncenter" width="600">
<img class="wp-image-46162 size-full" src="https://www.example.com/images/foo.jpg" alt="This describes the image" width="600" height="338" />
This is a caption about the image</wagtail_block_caption>
```

The original wordpress shortcode will be replaced with the custom html above.

### Block Creator example

The StreamField block json is created at the block builder stage. 

The get_block_json() method on the CaptionHandler() class will return the json for the StreamField block. The json is used at the BlockBuilder stage to create the StreamField block.

The StreamField block referenced in the json output will need a matching Wagtail block type in your app.

For example:

```python
# The Wagtail block included for the caption shortcode handler

class ImageBlock(blocks.StructBlock):
    image_file = ImageChooserBlock()
    caption = blocks.CharBlock(required=False)

    class Meta:
        icon = "image"
        template = "wagtail_wordpress_import/image_block.html"
```

## Creating you own shortcode handlers

Steps to create your own Block shortcode handlers.

**PART 1** Create a class that inherits from BlockShortcodeHandler()

For example: we need to create a shortcode handler to transform a `faqlist` Wordpress shortcode.

```python
# import the BlockShortcodeHandler
from wagtail_wordpress_import.prefilters.handle_shortcodes import BlockShortcodeHandler

# your shortcode handler
class FaqListShortcodeHandler(BlockShortcodeHandler):
  shortcode_name = 'faqlist'
```

Your class should include `shortcode_name` as a class property with a value of the shortcode name that you need to transform.


You will need to use a `@register` method provided to decorate your class so it will be added to the list of shortcode handlers.

```python
from wagtail_wordpress_import.prefilters.handle_shortcodes import register

@register("faqlist")
class FaqListShortcodeHandler(BlockShortcodeHandler):
  ...
```

*The name you use in the **register decorator** must match the shortcode name you need to transform.*

Your class will then perform the transformation of the Wordpress shortcode to a specific HTML tag with the name `wagtail_block_{shortcode_name}` during the import process.

The shortcode_name is used in a regular expression to search for the shortcodes in the HTML content.

If we are transforming a Wordpress shortcode with the name of `faqlist` the HTML tags will be named `wagtail_block_faqlist`.

**Part 2** Your class needs to create the StreamField json which is used to build the StreamField block during the import process.

Add a method to your class called `construct_block` which takes one parameter `wagtail_custom_html`

For example:

```python
  def construct_block(self, wagtail_custom_html):
    """
    wagtail_custom_html: is the new wagtail tag the 
    """

    # Do your processing here with something like BeautifulSoup or html.parser
    # The parsing you do here should output the attributes/values of the inner 
    # HTML content of wagtail_custom_html

    # You can only return a single block here
    # but your block can have other blocks as values
    return {
        "type": "[your_block_name]",
        "value": {
          # a dict with keys that your block requires 
        },
    }
```

**Part 3** The type of block in the json you return here will need a `real` block registered in your app and be available on the page model you are importing to.

### TODO: I will need to expand more here about the json return value. We will also need to follow through with the example of faqlist I think. I'll have a clearer picture of whats required after the next couple of tickets are complete
