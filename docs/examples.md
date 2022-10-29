# Examples

- [Examples](#examples)
  - [Creating a Wagtail Block for specific HTML structures](#creating-a-wagtail-block-for-specific-html-structures)
  - [How to implement a handler for a specific HTML structure](#how-to-implement-a-handler-for-a-specific-html-structure)
    - [Add extra configuration to allow this HTML tag to be passed through bleach_clean()](#add-extra-configuration-to-allow-this-html-tag-to-be-passed-through-bleach_clean)
    - [Loading your handler](#loading-your-handler)

## Creating a Wagtail Block for specific HTML structures

Some of the HTML content to be imported may contain HTML structures that are not well suited to be part of a RichText block.

For example, the code snippet below defines an anchor tag with an image inside it which would render as an image that's clickable to view some other content.

```html
<a href="http://www.example.com/some-content">
    <img 
        src="http;//www.example.com/image.jpg" 
        title="Image title" 
        class="alignleft"/>
</a>
```

Once imported, the content will be included inside a RichText block but the anchor around the image would be removed by Draftail if the page is edited in the Wagtail Admin.

The Draftail editor is able to handle many different types of content but if it's not possible to handle content types like the one above there's a chance that some data will be lost. You can read more about the content types supported by Draftail [here](https://docs.wagtail.io/en/stable/extending/rich_text_internals.html#rich-text-internals).

The package includes a class to convert WordPress block shortcodes to Wagtail blocks during the import, it's possible to use this class to transform content that is not a shortcode, but a specific HTML structure. This is done though the use of BeautifulSoup parsing the HTML rather than the provided regular expression that is part of a block shortcode handler.

## How to implement a handler for a specific HTML structure

The following handler will take some HTML input and convert all found specific HTML structures to a Wagtail block type.

```python
# anchor_image_handler.py


from bs4 import BeautifulSoup

from wagtail_wordpress_import.block_builder_defaults import get_or_save_image
from wagtail_wordpress_import.prefilters.handle_shortcodes import (
    BlockShortcodeHandler,
    register,
)


@register()
class AnchorImageHandler(BlockShortcodeHandler):
    # shortcode name is required and is used to create a unique HTML tag.
    shortcode_name = "anchor_image"

    def pre_filter(self, string):
        # This method is required and will be called to transform a specific
        # HTML structure found by BeautifulSoup into a custom HTML tag
        # This example would produce an HTML tag of <wagtail_block_anchor_image>
        soup = BeautifulSoup(string, "html.parser")
        anchor_tags = soup.find_all("a")

        anchors = []
        for anchor in anchor_tags:
            if anchor.find("img"):
                anchors.append(anchor)

        for a in anchors:
            attrs = {}
            attrs["data-src"] = a.find("img").attrs["src"]
            attrs["data-caption"] = a.find("img").attrs["title"]
            attrs["data-class"] = a.find("img").attrs["class"]
            attrs["data-href"] = a.attrs["href"]
            replacement_custom_tag = soup.new_tag(self.element_name)
            replacement_custom_tag.attrs = attrs
            a.replace_with(replacement_custom_tag)

        return str(soup)

    def construct_block(self, soup):
        # get_or_save_image() is not included in the shortcode handler
        # it is included in the package and can be used if required
        image_file = get_or_save_image(soup.attrs["data-src"])

        if image_file:
            # The block type as a dict is returned to the BlockBuilder
            return {
                "type": "image",
                "value": {
                    "image": image_file.id,
                    "caption": soup.attrs.get("data-caption"),
                    "alignment": soup.attrs.get("data-class"),
                    "link": soup.attrs.get("data-href"),
                },
            }
        else:
            # You should return at least one valid block here.
            # This returns a raw_html block containing the custom HTML tag.
            # It's a way to handle content that for some reason could not be parsed.
            # RawHTMLBlock provided by Wagtail https://docs.wagtail.io/en/latest/reference/streamfield/blocks.html#wagtail.core.blocks.RawHTMLBlock
            return {
                "type": "raw_html",
                "value": str(soup),
            }
```

Because the handler will add a custom HTML tag to the content the default action of the bleach_clean() filter needs to be altered.

Specifically, it needs to know what the custom HTML tag name is and what are valid attributes of the tag.

Then generated custom HTML tag for the example above would be:

```html
<wagtail_block_anchor_image 
    data-href="http://www.example.com/some-content" 
    data-class="alignleft" 
    data-src="http;//www.example.com/image.jpg" 
    data-caption="Image title">
</wagtail_block_anchor_image>
```

Before the custom HTML tag above is converted to a Wagtail block all the content is run through bleach_clean() to remove any unwanted HTML tags. The default list of HTML tags and attributes doesn't include the custom HTML here.

### Add extra configuration to allow this HTML tag to be passed through bleach_clean()

In your own settings add the following:

```python
WAGTAIL_WORDPRESS_IMPORT_PREFILTERS = [
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.linebreaks_wp",
    },
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.transform_shortcodes",
    },
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.transform_inline_styles",
    },
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.bleach_clean",
        "OPTIONS": {
            "ADDITIONAL_ALLOWED_ATTRIBUTES": {
                "wagtail_block_anchor_image": "data-caption",
                "wagtail_block_anchor_image": "data-class",
                "wagtail_block_anchor_image": "data-href",
                "wagtail_block_anchor_image": "data-src",
            },
        },
    },
]
```

The four `FUNCTIONS` are required to run the full list of prefilters and is copied here form the defaults in the package.

The specific `OPTIONS` for `ADDITIONAL_ALLOWED_ATTRIBUTES` are required for this example and will be added to the configuration of `wagtail_wordpress_import.prefilters.bleach_clean` so the custom HTML tag with those attributes will pass through bleach_clean() and be available to the block builder when it creates a ImageBlock()

### Loading your handler

If your handler is in a module that's not loaded during the import, you can add it to your apps.py `ready()` method:

```python
# pages.apps.py

from django.apps import AppConfig


class PagesConfig(AppConfig):
    name = "pages"

    def ready(self):
        from . import anchor_image_handler
```
