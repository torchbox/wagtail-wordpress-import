# Pre-Filtering HTML content

- [Pre-Filtering HTML content](#pre-filtering-html-content)
- [Why use pre-filters](#why-use-pre-filters)
- [Pre-filters](#pre-filters)
  - [Included pre-filters](#included-pre-filters)
  - [Pre-filter configuration](#pre-filter-configuration)
    - [Pre-filter running order](#pre-filter-running-order)
  - [Running order:](#running-order)
  - [Add your own pre-filter / options](#add-your-own-pre-filter--options)
  - [Create pre-filter methods](#create-pre-filter-methods)

# Why use pre-filters

Pre-filters provide transformations to be made on a page's content before it is used to build StreamField blocks. In the imported XML file, the page's content is available in each `<item><content:encoded />text content is here ...` element.

*For example, WordPress renders a double line break as separate paragraphs. The import process requires valid HTML rather than the plain text of the source XML. We have included a pre-filter that uses a Python implementation of the PHP script that's used in WordPress to convert two line breaks into `</p><p>`.*

---

# Pre-filters

Each time the importer processes a page, the body content is transformed by running a series of pre-filters in a specific order.

***Pre-Filter processes included***

1. double line break converted to paragraphs
2. inline styles transformer
3. HTML clean up filter

## Included pre-filters

---

-- **filter_linebreaks_wp()** [source](wagtail_wordpress_import/prefilters/linebreaks_wp_filter.py)

Converts double line breaks into paragraphs

This filter reimplements the `wpautop` PHP script into Python, to convert the raw HTML content into HTML content. It generally adds `<p>` tags around text that has no surrounding tag. Therefore the text lines in the filtered content will have a surround HTML tag in place if one was not already included.

---

-- **filter_transform_inline_styles()** [source](wagtail_wordpress_import/prefilters/transform_styles_filter.py)

This filter converts any inline style rules to their corresponding HTML tags where possible (e.g. bold and italic text). Otherwise it converts alignment style rules to CSS classes.

*e.g:*

```html
<span style="font-weight: bold;>some text</span>
```
is converted to 
```html
<b>some text</b>
```
and 
```html
<p style="text-align: left;>some text</p>
```
is converted to
```html
<p class="align-left">some text</p>

```

The outcome of these transformations helps us normalize the content that's likely to become part of a `RichText()` field

---

-- **filter_bleach_clean()** [source](wagtail_wordpress_import/prefilters/bleach_filter.py)

This filter removes tags that aren't included in range of `ALLOWED_TAGS`, `ALLOWED_ATTRIBUTES` and `ALLOWED_STYLES` configuration settings.

It's possible to add new settings to this configuration to suit your own use case. We provide a sensible range to cover most use cases.

---

## Pre-filter configuration

The package includes the pre-filters listed above. An initial setup of the package will include them in the import process.

### Pre-filter running order

The order the pre-filters are run will have an impact on the final HTML output.

Each pre-filter takes the output from the previous pre-filter, with the exception of the first pre-filter which receives the raw content. 

The output of the last pre-filter is used to build the stream field blocks in a later process.

## Running order: 
It's possible to change the pre-filter running order by changing the order of the defaults provided.

Add the below settings to your  own settings file and change the order of the list items

```python
WAGTAIL_WORDPRESS_IMPORT_PREFILTERS = [
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.linebreaks_wp",
    },
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.transform_inline_styles",
    },
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.bleach_clean",
    },
]
```

## Add your own pre-filter / options

Add the above settings to your own settings file and include the new pre-filter. *It's possible to exclude a pre-filter by removing it from the list.*

e.g: Using `custom options` in the bleach filter
```python

WAGTAIL_WORDPRESS_IMPORT_PREFILTERS = [
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.linebreaks_wp",
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

Here `my-custom-tag` would be appended to the `ALLOWED_TAGS` in the bleach_filters

To provide your own pre-filter add:

```python
{
    "FUNCTION": "my_app.my_prefilters.my_filter",
},
```
at the position to match the running order you need. *It's possible to include an `OPTIONS` key for your own pre-filter which will be passed into your pre-filter method*

## Create pre-filter methods

You can find the provided pre-filters [here](wagtail_wordpress_import/prefilters)

To create your own pre-filter you need to create a module with a function in your app with the following signature:

```python
def filter_func(input_content, options=None):
    """
    params: 
    
    input_content:
        HTML (most likely a string but depends on your requirements)

    options:
        always pass this in even if it's not required

    return: 
        most likely a string most likely a string but depends on your requirements.
        this would be passed to the next pre-filter or if it's the final pre-filter
        it will be passed to the next import process.
    """

    # implement your own transformations/parsing here
    output_content = ...

    return output_content
```

Then you need to include the pre-filter in your own custom config at the position you need it to run.

e.g.
```python
WAGTAIL_WORDPRESS_IMPORT_PREFILTERS = [
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.linebreaks_wp",
    },
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.transform_inline_styles",
    },
    {
        "FUNCTION": "my_app.my_prefilters.my_filter", << new pre-filter
    },
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.bleach_clean",
        "OPTIONS": {
            "ADDITIONAL_ALLOWED_TAGS": ["my-custom-tag"]
        }
        
    },
]
```
