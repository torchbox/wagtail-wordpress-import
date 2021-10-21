from bs4 import BeautifulSoup
from django.utils.module_loading import import_string
from wagtail_wordpress_import.prefilters.transform_styles_defaults import (
    conf_styles_mapping,
    conf_transform_html_tags_enabled,
    conf_transform_html_tags_mapping,
    HTML_TAGS,
)


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

    CONF_STYLES_MAPPING = conf_styles_mapping()
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

    if conf_transform_html_tags_enabled():
        for filter in conf_transform_html_tags_mapping():
            tags = soup.findAll(filter[0])

            for tag in tags:
                filter[1](soup, tag)

    return str(soup)
