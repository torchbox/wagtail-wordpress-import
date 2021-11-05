# Pre-Filtering HTML content

- [Pre-Filtering HTML content](#pre-filtering-html-content)
  - [Why use pre-filters](#why-use-pre-filters)
  - [How Pre-filters work](#how-pre-filters-work)
    - [Included Pre-Filters](#included-pre-filters)
    - [Pre-filter configuration](#pre-filter-configuration)
    - [Add your own pre-filter options to an existing pre-filter](#add-your-own-pre-filter-options-to-an-existing-pre-filter)
  - [Create your own pre-filter](#create-your-own-pre-filter)

## Why use pre-filters

Pre-filters transform the page body content before it is used to build StreamField blocks. See [Pre-Filters included](#pre-filters-included)

For example: WordPress renders a double line break as separate paragraphs. `wagtail_wordpress_import/prefilters/linebreaks_wp_filter.py` is a Python implementation of the Wordpress double line breaks converter. It converts the double line breaks to paragraphs by wrapping the text content in a `<p>` HTML tag.

Transforming the body content, during the import process, into well formed HTML means it can be easily converted into specific StreamField blocks.

---

## How Pre-filters work

Each time the Wordpress importer processes a page, the body content is transformed by a series of pre-filters in a specific order.

### Included Pre-Filters

1. Double line breaks to paragraphs
2. Inline styles transformer
3. Wordpress shortcode converter
4. HTML clean up filter (bleach)

---

-- **filter_linebreaks_wp()** [source](wagtail_wordpress_import/prefilters/linebreaks_wp_filter.py)

Converts double line breaks into paragraphs

This filter re-implements the `wpautop` PHP script using Python. It generally adds `<p>` tags around text that has no surrounding tag. Therefore the lines of text will have a surround HTML tag in place if one was not already included.

---

-- **filter_transform_inline_styles()** [source](wagtail_wordpress_import/prefilters/transform_styles_filter.py)

This filter converts any inline style rules to their corresponding HTML tags where possible.

HTML elements with style rules for bold or italic are converted to `<b>` or `<i>` HTML tags. HTML elements with style rules for alignment are converted to CSS classes.

For Example:

```html
<span style="font-weight: bold;">some text</span>
```

is converted to

```html
<b>some text</b>
```

and

```html
<p style="text-align: left;">some text</p>
```

is converted to

```html
<p class="align-left">some text</p>

```

---

-- **filter_transform_shortcodes()** [source](wagtail-wordpress-import/wagtail_wordpress_import/prefilters/handle_shortcodes.py)

This filter will parse the body content for Wordpress shortcodes and convert them to a custom HTML tag which is later converted to a `complex` StreamField block type. [See shortcode documentation](wagtail-wordpress-import/docs/shortcodes.md)

-- **filter_bleach_clean()** [source](wagtail_wordpress_import/prefilters/bleach_filter.py)

This is the last pre-filter to be run on the content. It removes HTML tags and attributes that aren't included in a range of `ALLOWED_TAGS`, `ALLOWED_ATTRIBUTES` and `ALLOWED_STYLES` configuration settings.

It's possible to add new Tags and Attributes to the configuration to suit your own use case. For the use of bleach's configuration options, see https://bleach.readthedocs.io/en/latest/.

---

### Pre-filter configuration

The prefilters listed above are all run during the import by default. They are run in the order below, top to bottom.

Default pre-filter configuration:

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
        },
    ]
```

The order the pre-filters are run will have an impact on the final HTML output. *If you change the order or exclude filters you may see unexpected results with the block building process.*

Each pre-filter receives the output from the previous pre-filter, with the exception of the first pre-filter which receives the raw content.

The output of the last pre-filter is passed to block builder to create the StreamField blocks JSON.

### Add your own pre-filter options to an existing pre-filter

Add `WAGTAIL_WORDPRESS_IMPORT_PREFILTERS` to your own settings file and include the new pre-filter. *It's possible to exclude a pre-filter by removing it from the list.*

All filters can be passed an `OPTIONS` dict but it's currently only useful for the bleach filter.

For example: Using custom options in the bleach filter

```python
WAGTAIL_WORDPRESS_IMPORT_PREFILTERS = [
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.linebreaks_wp",
    },
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.transform_inline_styles",
    },
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.transform_inline_styles",
    },
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.bleach_clean",
        "OPTIONS": {
            "ADDITIONAL_ALLOWED_TAGS": ["my-custom-tag"]
        }
        
    },
]
```

Here `my-custom-tag` would be appended to the `ALLOWED_TAGS` in the bleach_filters and would not be escaped or removed from the final HTML

To provide your own pre-filter add a new item to the configuration with the key FUNCTION and value is the dotted path to the function to be called.

```python
{
    "FUNCTION": "my_app.my_prefilters.my_filter",
},
```

Add it at the position to match the running order you need. *It's possible to include an `OPTIONS` key for your own pre-filter which will be passed into your pre-filter method*

## Create your own pre-filter

You can find the provided pre-filters [here](wagtail_wordpress_import/prefilters) They are a good source of examples to create your own pre-filter.

To create your own pre-filter you need to create a module with a function in your app with the following signature:

```python
# your function should always begin with `filter_`
def filter_func(input_content, options=None):
    """Takes input generally as a string and returns the the modified input as a string.

    input_content: most likely a HTML string but depends on your requirements

    options: can be passed to suit you own use case

    return: the modified input as a string
    """

    # implement your own transformations/parsing here

    return a_string
```
