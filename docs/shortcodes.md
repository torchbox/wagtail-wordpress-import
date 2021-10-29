# Wordpress shortcodes block converter

- [Wordpress shortcodes block converter](#wordpress-shortcodes-block-converter)
- [Shortcode classes](#shortcode-classes)
- [Included shortcode handlers](#included-shortcode-handlers)
  - [Caption shortcode](#caption-shortcode)
    - [Pre-filter example:](#pre-filter-example)
    - [Block Creator example](#block-creator-example)
- [Creating you own shortcode handlers.](#creating-you-own-shortcode-handlers)

# Shortcode classes

The package is able to parse Wordpress shortcodes. 

We provide a base class `BlockShortcodeHandler` that performs the transformation of the raw shortcode into a custom HTML tag using regular expressions.

The custom HTML tag will retain all the parts of the original shortcode which you can make use of when creating the StreamBlock json.

---

# Included shortcode handlers

## Caption shortcode

The package includes a shortcode handler for Wordpress `caption` shortcodes. The handler pre-filter will transform the shortcode into a custom HTML tag. 

The transformation happens in the pre-filter method of the CaptionHandler class.

### Pre-filter example:

*Wordpress shortcode*

```html
[caption id="attachment_46162" align="aligncenter" width="600"]
<img class="wp-image-46162 size-full" src="https://www.example.com/images/foo.jpg" alt="This describes the image" width="600" height="338" />
This is a caption about the image[/caption]
```

*will be transformed to*

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

# Creating you own shortcode handlers.

This part of the docs it to be completed later...
