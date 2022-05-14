import re

from bs4 import BeautifulSoup
from django.utils.module_loading import import_string

from wagtail_wordpress_import.prefilters.transform_styles_defaults import (
    HTML_TAGS,
    conf_transform_html_tags_enabled,
    conf_transform_html_tags_mapping,
    transform_float_left,
    transform_float_right,
    transform_style_bold,
    transform_style_bold_italic,
    transform_style_center,
    transform_style_italic,
    transform_style_left,
    transform_style_right,
)

CONF_STYLES_MAPPING = [
    (
        re.compile(r"font-style:italic;font-weight:bold;", re.IGNORECASE),
        transform_style_bold_italic,
    ),
    (re.compile(r"font-weight:bold;", re.IGNORECASE), transform_style_bold),
    (re.compile(r"font-style:italic;", re.IGNORECASE), transform_style_italic),
    (
        re.compile(
            r"text-align:center;",
            re.IGNORECASE,
        ),
        transform_style_center,
    ),
    (re.compile(r"text-align:left;", re.IGNORECASE), transform_style_left),
    (re.compile(r"text-align:right;", re.IGNORECASE), transform_style_right),
    (re.compile(r"float:left;", re.IGNORECASE), transform_float_left),
    (re.compile(r"float:right;", re.IGNORECASE), transform_float_right),
]


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
    if options and options.get("HTML_TAGS"):
        html_tags = import_string(options["HTML_TAGS"])
        if callable(html_tags):
            CONF_HTML_TAGS = html_tags()
        else:
            CONF_HTML_TAGS = html_tags

    styles_mapping = CONF_STYLES_MAPPING

    if options and "TRANSFORM_STYLES_MAPPING" in options:
        styles_mapping = options["TRANSFORM_STYLES_MAPPING"]
        for filter in styles_mapping:
            filter_transform_styles(
                soup.findAll(style=filter[0]),
                soup,
                import_string(filter[1]),
                CONF_HTML_TAGS,
            )
    else:
        for filter in styles_mapping:
            filter_transform_styles(
                soup.findAll(style=filter[0]), soup, filter[1], CONF_HTML_TAGS
            )

    if conf_transform_html_tags_enabled():
        for filter in conf_transform_html_tags_mapping():
            tags = soup.findAll(filter[0])

            for tag in tags:
                filter[1](soup, tag)

    return str(soup)


def filter_transform_styles(tags, soup, filter_method, conf_html_tags):
    for tag in tags:
        if tag.name not in conf_html_tags:
            print("item.name = tag not found in HTML_TAGS")

        filter_method(soup, tag)
