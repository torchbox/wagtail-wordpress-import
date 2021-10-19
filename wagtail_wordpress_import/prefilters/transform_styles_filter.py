import re

from bs4 import BeautifulSoup
from django.conf import settings
from django.utils.module_loading import import_string


def normalize_style_attrs(soup):
    """
    Normalize the style attrs on tags so we have a predictable format for parsing.

    e.g. font-style: italic becomes font-style:italic;
    e.g. FONT-WEIGHT:400; becomes font-weight:400;
    e.g. font-weight: bold;font-style:italic; becomes font-style:italic;font-weight:bold;
    The style rules are all lowercased, with `;` appended and have no spaces.
    Spaces are removed between multiple style rules.
    Style rules are sorted alphabetically

    The styles attrs won't exist in the final page content they are removed later on
    in filter_bleach_clean() method, they are kept around for any other processing needs.
    """

    elements = soup.findAll(recursive=True)

    for el in elements:
        if el.attrs and el.attrs.get("style"):
            styles_list = [
                style.strip().lower().replace(" ", "") + ";"
                for style in el.attrs["style"].split(";")
                if style != ""
            ]
            el.attrs["style"] = "".join(sorted(styles_list))

    return soup


def filter_transform_inline_styles(html, options=None):
    """
    Use the default or provided CONFIG to loop through each filter
    and apply the transform_* method

    params
        html: raw html input, the input needs to be valid html
        options: allows a developer to override the default config
        and pass in HTML_TAGS and TRANSFORM_STYLES_MAPPING
    """

    soup = normalize_style_attrs(BeautifulSoup(html, "html.parser"))

    CONF_HTML_TAGS = HTML_TAGS
    if options and options["CONFIG"].get("HTML_TAGS"):
        html_tags = import_string(options["CONFIG"]["HTML_TAGS"])
        if callable(html_tags):
            CONF_HTML_TAGS = html_tags()
        else:
            CONF_HTML_TAGS = html_tags

    CONF_STYLES_MAPPING = TRANSFORM_STYLES_MAPPING
    if options and options["CONFIG"].get("TRANSFORM_STYLES_MAPPING"):
        styles_mapping = import_string(options["CONFIG"]["TRANSFORM_STYLES_MAPPING"])
        if callable(styles_mapping):
            CONF_STYLES_MAPPING = styles_mapping()
        else:
            CONF_STYLES_MAPPING = styles_mapping

    for filter in CONF_STYLES_MAPPING:
        tags = soup.findAll(style=filter[0])

        for tag in tags:
            if tag.name not in CONF_HTML_TAGS:
                print("item.name = tag not found in HTML_TAGS")

            filter[1](soup, tag)

    transform_html_tags_enabled = getattr(
        settings,
        "WAGTAIL_WORDPRESS_IMPORT_TRANSFORM_HTML_TAGS_ENABLED",
        TRANSFORM_HTML_TAGS_ENABLED,
    )

    transform_html_tags_mapping = getattr(
        settings,
        "WAGTAIL_WORDPRESS_IMPORT_TRANSFORM_HTML_TAGS_MAPPING",
        TRANSFORM_HTML_TAGS_MAPPING,
    )

    if transform_html_tags_enabled:
        for filter in transform_html_tags_mapping:
            tags = soup.findAll(filter[0])

            for tag in tags:
                filter[1](soup, tag)

    return str(soup)


def transform_style_bold(soup, tag):
    """
    replace the input tag name with `b`
    and add the existing attrs["style"] to
    the new tag
    """
    new_tag = soup.new_tag("b")
    new_tag.attrs["style"] = tag.attrs["style"]
    new_tag.string = tag.text
    tag.replace_with(new_tag)


def transform_style_italic(soup, tag):
    """
    replace the input tag name with `b`
    and add the existing attrs["style"] to
    the new tag

    there are instances of <i> tag inside a <b> tag
    preseve the <b> tag and add the <i> tag as a child
    e.g. <b><i>text</i></b>
    """

    if not tag.name == "b":
        new_tag = soup.new_tag("i")
        new_tag.string = tag.text
        new_tag.attrs["style"] = tag.attrs["style"]
        tag.replace_with(new_tag)

    elif tag.name == "b":
        new_tag = soup.new_tag("i")
        new_tag.string = tag.text
        new_tag.attrs["style"] = tag.attrs["style"]
        tag.string = ""
        tag.append(new_tag)


def transform_style_center(soup, tag):
    """
    apply a new css class to any existing classes
    """
    _class = tag.get("class", "") + " align-center"
    tag.attrs["class"] = _class.strip()


def transform_style_left(soup, tag):
    """
    apply a new css class to any existing classes
    """
    _class = tag.get("class", "") + " align-left"
    tag.attrs["class"] = _class.strip()


def transform_style_right(soup, tag):
    """
    apply a new css class to any existing classes
    """
    _class = tag.get("class", "") + " align-right"
    tag.attrs["class"] = _class.strip()


def transform_float_left(soup, tag):
    """
    apply a new css class to any existing classes
    """
    _class = tag.get("class", "") + " float-left"
    tag.attrs["class"] = _class.strip()


def transform_float_right(soup, tag):
    """
    apply a new css class to any existing classes
    """
    _class = tag.get("class", "") + " float-right"
    tag.attrs["class"] = _class.strip()


def transform_html_tag_strong(soup, tag):
    """
    replace the input tag name of `strong` with `b`
    """
    tag.name = "b"


def transform_html_tag_em(soup, tag):
    """
    replace the input tag name of `em` with `i`
    """
    tag.name = "i"


"""
Its intended that a developer can override TRANSFORM_STYLES_MAPPING
and provide their own style rules to match for by adding WAGTAIL_WORDPRESS_IMPORT_PREFILTERS
to their own settings

# example WAGTAIL_WORDPRESS_IMPORT_PREFILTERS config in your own settings is below

WAGTAIL_WORDPRESS_IMPORT_PREFILTERS = [
    {"FUNCTION": "wagtail_wordpress_import.prefilters.linebreaks_wp_filter",},
    {"FUNCTION": "wagtail_wordpress_import.prefilters.transform_styles_filter",},
    {"FUNCTION": "prefilters.bleach_clean.clean",
        "OPTIONS": {
            "ADDITIONAL_ALLOWED_TAGS": ["h1", "h2", ...],
            "ADDITIONAL_ALLOWED_ATTRIBUTES": ["style", "class", "data-attr", ...],
            "ADDITIONAL_ALLOWED_STYLES": ["font-weight: bold", "font-style: italic", ...],
        },
    },
]

The prefilters are run in the order of the list above.
If you don't need a filter to run you can remove it from the list.
If you need another filter to run you can include it in the list and will need
to provide the filter module in your own wagtail site

See the documentation in this repo for further help with creating filters
"""
TRANSFORM_STYLES_MAPPING = [
    (re.compile(r"font-weight:bold*", re.IGNORECASE), transform_style_bold),
    (re.compile(r"font-style:italic*", re.IGNORECASE), transform_style_italic),
    (
        re.compile(
            r"text-align:center*",
            re.IGNORECASE,
        ),
        transform_style_center,
    ),
    (re.compile(r"text-align:left*", re.IGNORECASE), transform_style_left),
    (re.compile(r"text-align:right*", re.IGNORECASE), transform_style_right),
    (re.compile(r"float:left*", re.IGNORECASE), transform_float_left),
    (re.compile(r"float:right*", re.IGNORECASE), transform_float_right),
]

"""
Its intended that a developer can override TRANSFORM_HTML_TAGS_MAPPING
and provide their own tag rules

# example WAGTAIL_WORDPRESS_IMPORT_TRANSFORM_HTML_TAGS_MAPPING config in your own settings is below

WAGTAIL_WORDPRESS_IMPORT_TRANSFORM_HTML_TAGS_MAPPING [
    ("strong", transform_html_tag_strong),
    ("em", transform_html_tag_em),
]

The tag filters can be listed in any order.
If you don't need a tag filter to run you can remove it from the list.
If you need another filter to run you can include it in the list and will need
to provide the filter method in your own wagtail site

See the documentation in this repo for further help with creating tag filters
"""
TRANSFORM_HTML_TAGS_MAPPING = [
    ("strong", transform_html_tag_strong),
    ("em", transform_html_tag_em),
]

"""
In your own settings you can disable the transformation of HTML tags using

WAGTAIL_WORDPRESS_IMPORT_TRANSFORM_HTML_TAGS_MAPPING = False
"""
TRANSFORM_HTML_TAGS_ENABLED = getattr(
    settings, "WAGTAIL_WORDPRESS_IMPORT_TRANSFORM_HTML_TAGS_ENABLED", True
)


HTML_TAGS = [
    "address",
    "article",
    "aside",
    "blockquote",
    "canvas",
    "dd",
    "div",
    "dl",
    "dt",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "noscript",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "tfoot",
    "ul",
    "video",
    "a",
    "abbr",
    "acronym",
    "b",
    "bdo",
    "big",
    "br",
    "button",
    "center",
    "cite",
    "code",
    "dfn",
    "em",
    "i",
    "img",
    "input",
    "kbd",
    "label",
    "map",
    "object",
    "output",
    "q",
    "samp",
    "script",
    "select",
    "small",
    "span",
    "strong",
    "sub",
    "sup",
    "textarea",
    "time",
    "tt",
    "var",
]
