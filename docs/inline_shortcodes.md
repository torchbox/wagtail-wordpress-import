# Converting Wordpress inline shortcodes for Draftail editor

- [Converting Wordpress inline shortcodes for Draftail editor](#converting-wordpress-inline-shortcodes-for-draftail-editor)
  - [Shortcode handler class](#shortcode-handler-class)
  - [How to create your own inline shortcode handler](#how-to-create-your-own-inline-shortcode-handler)
  - [An example of how to add a shortcode handler for the Draftail editor](#an-example-of-how-to-add-a-shortcode-handler-for-the-draftail-editor)
    - [Stock inline shortcode handler class](#stock-inline-shortcode-handler-class)
    - [Stock inline shortcode handler configuration](#stock-inline-shortcode-handler-configuration)
  - [How to test this example works](#how-to-test-this-example-works)

## Shortcode handler class

The package is able to transform Wordpress inline shortcodes.

We provide a base class [InlineShortcodeHandler](/wagtail-wordpress-import/wagtail_wordpress_import/handle_inline_shortcodes.py) that performs regular expression search for a shortcode.

## How to create your own inline shortcode handler

1. Create a subclass of InlineShortcodeHandler.
2. Extend the Draftail editor to recognise the new HTML tag that your shortcode handler will generate.

## An example of how to add a shortcode handler for the Draftail editor

Extending the Draftail editor is fully documented in the [Wagtail Documentation](https://docs.wagtail.io/en/stable/extending/extending_draftail.html).

This example will enable the stock chooser display in the Draftail editor. It's a fully functioning but somewhat fictional example but should help you get started with your own inline shortcode handler.

The complete Wagtail Documentation example can be [Viewed Here](https://docs.wagtail.io/en/stable/extending/extending_draftail.html#creating-new-entities) and this is the first step you should take to get the example working in your own project.

We assume here that you are importing HTML that will be part of a RichText block, and that the HTML contains an inline shortcode `[stock symbol="TSLA"]`, that you want to be editable in the Draftail editor, and to be displayed in the rendered page.

The WordPress shortcode will be transformed during the import, from `[stock symbol="TSLA"]` to `<span data-stock="TSLA">$TSLA</span>` before being saved to the RichText block.

You will only need to write one class to handle a shortcode like this. The symbol is dynamic and can be different across multiple shortcodes in the same HTML content.

All shortcodes of the type `[stock symbol="any-valid-symbol"]` will be transformed.

### Stock inline shortcode handler class

```python
# you can give this module any name or add the class to an existing module

# import the base handler class
from wagtail_wordpress_import.handle_inline_shortcodes import (
    InlineShortcodeHandler, 
)


# Subclasses should declare a shortcode_name and provide
# a construct_html_tag method for converting the shortcode to a HTML tag.
class StockHandler(InlineShortcodeHandler):
    """
    The Wordpress shortcode is replaced by a custom HTML tag. 
    The shortcode attributes are preserved and can be included in the custom HTML tag.

    Sample wordpress stock shortcode:
    [stock symbol="TSLA"]

    all matching shortcodes are replaced by:

    <span data-stock="TSLA">$TSLA</span>
    """

    # The shortcode name that is after the first "[" and the 
    # matching for the shortcode name will end at the first space
    shortcode_name = "stock"

    """You must implement this method in your own class"""
    def construct_html_tag(self, html):
        # It will receive the `html` string content of the RichText block

        """ This is fully functioning code for the stock example. You may need 
        to use your own logic here depending on your requirements.
        
        The output needs be the `html` string received with the  modifications 
        your code makes.
        """

        matches = self._pattern.finditer(html) # find all matches of the shortcode

        for match in matches: # Loop through the matches

            # Get the shortcode attributes using the parent class method
            # or you can implement your own method for this.
            attrs = self.get_shortcode_attrs(match.groupdict()["attrs"])

            # Modify the `html` string by replacing the shortcode with a HTML tag.
            html = html.replace(
                match.group(),
                f'<{self.element_name} data-{self.shortcode_name}="{attrs["symbol"]}">${attrs["symbol"]}</{self.element_name}>',
            )

        return html # always return the modified `html` as a string

# Provide a reference to the class thats equal to the last part of your 
# configuration dotted path. See configuration example below.
stock_handler = StockHandler()
```

### Stock inline shortcode handler configuration

Add the following configuration to your own settings.

```python
WAGTAIL_WORDPRESS_IMPORTER_INLINE_SHORTCODE_HANDLERS = [
    "path.to.your.stock_handler",
]
```

The package will always call the `construct_html_tag` method of you handler class.

## How to test this example works

Find an `item` in the XML file you are importing and add a stock shortcode of `[stock symbol="TSLA"]` to the `<content:encoded></content:encoded>` tag. The stock shortcode can be inline within a piece of text or on its own line.

Now run the import command. When the command completes check the RichText content for the page you added the stock shortcode to. It should be visible in the editor just as if you had used the toolbar button to add a stock symbol.

If you have implemented the front end part of the Wagtail example (the last JavaScript code snippet) you should also see the stock symbol graph.
