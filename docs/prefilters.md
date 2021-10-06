# Pre-Filtering HTML content

- [Pre-Filtering HTML content](#pre-filtering-html-content)
- [Why use pre-filters](#why-use-pre-filters)
- [Pre-filters](#pre-filters)
  - [Available filters](#available-filters)
  - [Pre-filter running order](#pre-filter-running-order)
  - [Running order:](#running-order)
  - [Configuration](#configuration)
  - [Defaults](#defaults)
  - [Create pre-filters](#create-pre-filters)
- [Pre-filter tools](#pre-filter-tools)
    - [Turn off debugging](#turn-off-debugging)

# Why use pre-filters

Each item (e.g. page or post) represented in the XML file has content intended for the body of a page that could include WYSIWYG content as well as short-codes.

That content isn't suitable in it's raw form for parsing and creating a range of stream fields or to be added to a single rich text field.

- HTML content can contain inline styles which could be created by WYSIWYG tools or manually entered
- Tables could be present
- Forms could be present
- List could be present
- and more

We do know that the html is going to be suitable for parsing using python built-ins
and other third party packages and be manipulated to better suit the requirements of the import and page creation process in wagtail.

---

# Pre-filters

Each time the import processes the body content of a page a series of filters are run on the content to transform it.

***Pre-Filters included***

1. linebreaks_wp_filter.py: this is a [python implementation](https://gist.github.com/albertsun/1160201/0a1f7d7a509fbcfa580725ed3783a29af51b62b4) of the wordpress function wpauto
2. normalize_styles_filter.py: using [BeautifulSoup](https://www.crummy.com/software/)
3. fix_styles_filter.py: using [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
4. bleach_filter.py: using [bleach](https://github.com/mozilla/bleach)

**The above filters run, by default, in the order above before the content is passed into the page model or parsed to stream field blocks.**

## Available filters

-- **filter_linebreaks_wp()**

`wagtail_wordpress_import/prefilters/linebreaks_wp_filter.py`

Wordpress uses line breaks as a mechanism for vertical spacing of rendered HTML (paragraphs) as an example. 

This filter implements the same process as `wpauto` to convert the raw html content into html content  with tags around every piece of content. It avoids changing anything that is acceptable. In the end it mostly deals adds `<p>` tags around text that has no surrounding tag.

-- **filter_normalize_style_attrs()**

`wagtail_wordpress_import/prefilters/normalize_styles_filter.py`

This filter converts inline style attributes to a format we can work with in the next filter because the format of style attributes can be different in some for each tag. It deals with word-case, spacing and closing `;`

-- **filter_fix_styles()**

`wagtail_wordpress_import/prefilters/fix_styles_filter.py`

This filter applies any inline style to the html tag that is useful in the context of the Wagtail rich text editor. It performs wrapping a tag around a piece of text as well ass applying classes to a tag to represent alignment.

Examples:

- `font-weigh:bold;` is better represented using a `<b>` tag
- `float: left;` is better represented by a class of `left-align`

-- **filter_bleach_clean()**

`wagtail_wordpress_import/prefilters/bleach_filter.py`

This filter is run last and removes tags based on a range of `ALLOWED` Tags, Attributes and Styles.

---

## Pre-filter running order

The order the pre-filters are run will have an impact on the final html output. The default order is:

    1. filter_linebreaks_wp()
    2. filter_normalize_style_attrs()
    3. filter_fix_styles()
    4. filter_bleach_clean()

Each pre-filter takes the output from the previous pre-filter, with the exception of the first pre-filter which receives the raw content. 

The output of the last pre-filter is used to build the stream field blocks in a later process.

## Running order: 
It's possible to change the pre-filter running order by altering the order of the `DEFAULT_PREFILTERS` provided by adding `WAGTAIL_WORDPRESS_IMPORT_PREFILTERS` to your  own settings file.

Some pre-filters can be given `OPTIONS` to alter the way the pre-filter behaves.

## Configuration

You can use the package without providing any configuration for pre-filters. We provide a small number of useful pre-filters that process html content before it's used to build out the stream field blocks.

## Defaults

**Pre-filter Default**:

```python
DEFAULT_PREFILTERS = [
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.linebreaks_wp_filter.filter_linebreaks_wp",
    },
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.normalize_styles_filter.filter_normalize_style_attrs",
    },
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.fix_styles_filter.filter_fix_styles",
    },
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.bleach_filter.filter_bleach_clean",
    },
]
```

**To change the configuration:**

copy the `DEFAULT_PREFILTERS` above to your own settings file and change the name to 
`WAGTAIL_WORDPRESS_IMPORT_PREFILTERS`

Example: using custom options in the bleach filter
```python

WAGTAIL_WORDPRESS_IMPORT_PREFILTERS = [
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.linebreaks_wp_filter.filter_linebreaks_wp",
    },
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.normalize_styles_filter.filter_normalize_style_attrs",
    },
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.fix_styles_filter.filter_fix_styles",
    },
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.bleach_filter.filter_bleach_clean",
        "OPTIONS": {
            "ADDITIONAL_ALLOWED_TAGS": ["my-custom-tag"]
        }
    },
]
```
`my-custom-tag` would be appended to the `ALLOWED_TAGS` in the bleach_filters

or provide your own pre-filter add:

```python
{
    "FUNCTION": "[app].[file].[method]",
},
```
at the position to match the running order you need. `[app].[file].[method]` is the  dotted path to your function.

**If you don't need any of the provided pre-filters you can exclude them from the config**

## Create pre-filters

You can find the provided pre-filters [here](wagtail_wordpress_import/prefilters)

To create your own pre-filter you need to create a function in your app with the following signature:

```python
def filter_func(input_content, options=None):
    """
    params: 
    
    input_content
    most likely a string but depending on your implementation 
    could be any type that you need to work with

    options:
    you probably won't need to pass in any options 
    in your own function but the signature requires the 
    parameter to be included

    return: 
    most likely a string but depending on your implementation 
    could be any type that you need to work with
    """

    # implement your own transformations/parsing here
    output_content = ...

    return output_content
```

Then you need to include the pre-filter in your own custom config at the position you need it to run. [See here](#defaults)

---

# Pre-filter tools

If you use the provided `WPImportedPageMixin` it has fields to receive the output from each pre-filter step which can be see on the Debug tab when editing a page. [Read about the mixin](models.md)

```
DEBUG_ENABLED = getattr(settings, 'WAGTAIL_WORDPRESS_IMPORT_DEBUG', True)
```

The debugging is on by default. 

If you are not using the provided page mixin then turn off debugging

### Turn off debugging

copy the config above to your own settings file and change the name to 
`WAGTAIL_WORDPRESS_IMPORT_DEBUG` and Set it's value to `False`
