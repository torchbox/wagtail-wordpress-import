import re

from bs4 import BeautifulSoup
from django.conf import settings
from django.utils.module_loading import import_string


def normalize_style_attrs(html, options=None):
    """
    There are different ways that styles are formatted coming out of wordpress.
    This normalizes them so the know what the format is for later parsing.

    e.g. font-style: italic becomes font-style:italic;
    e.g. FONT-WEIGHT:400; becomes font-weight:400;

    So essentially the styles are all lowercased, with appended ; and have no spaces.
    Worth noting that these styles are actually removed later on when the fix_styles
    method is run so if they look wrong it's OK here as they are a `template`

    param: `options` NOT IMPLEMENTED
    """
    soup = BeautifulSoup(html, "html.parser")
    elements = soup.findAll(recursive=True)

    for el in elements:
        if el.attrs and el.attrs.get("style"):
            styles_list = [
                style.strip().lower().replace(" ", "") + ";"
                for style in el.attrs["style"].split(";")
                if style != ""
            ]
            el.attrs["style"] = " ".join(sorted(styles_list))

    return str(soup)


def filter_transform_inline_styles_to_tags(html, options=None):

    CONF_HTML_TAGS = HTML_TAGS
    if options and options["CONFIG"].get("HTML_TAGS"):
        html_tags = import_string(options["CONFIG"]["HTML_TAGS"])
        if callable(html_tags):
            CONF_HTML_TAGS = html_tags()
        else:
            CONF_HTML_TAGS = html_tags

    CONF_STYLES_MAPPING = TRANSFORM_STYLES_MAPPING
    if options and options["CONFIG"].get("FILTER_MAPPING"):
        styles_mapping = import_string(options["CONFIG"]["FILTER_MAPPING"])
        if callable(styles_mapping):
            CONF_STYLES_MAPPING = styles_mapping()
        else:
            CONF_STYLES_MAPPING = styles_mapping

    soup = BeautifulSoup(normalize_style_attrs(html), "html.parser")

    for filter in CONF_STYLES_MAPPING:
        tags = soup.findAll(style=filter[0])

        for tag in tags:
            if tag.name not in CONF_HTML_TAGS:
                print("item.name = tag not found in HTML_TAGS")

            filter[1](soup, tag)

    if TRANSFORM_TAGS_ENABLED:
        for filter in TRANSFORM_TAGS_MAPPING:
            tags = soup.findAll(filter[0])

            for tag in tags:
                filter[1](soup, tag)

    return str(soup)


def transform_style_bold(soup, tag):

    new_tag = soup.new_tag("b")
    new_tag.attrs["style"] = tag.attrs["style"]
    new_tag.string = tag.text
    tag.replace_with(new_tag)


def transform_style_italic(soup, tag):
    """
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
    _class = tag.get("class", "") + " align-center"
    tag.attrs["class"] = _class.strip()


def transform_style_left(soup, tag):
    _class = tag.get("class", "") + " align-left"
    tag.attrs["class"] = _class.strip()


def transform_style_right(soup, tag):
    _class = tag.get("class", "") + " align-right"
    tag.attrs["class"] = _class.strip()


def transform_tag_strong(soup, tag):
    tag.name = "b"


def transform_tag_em(soup, tag):
    tag.name = "i"


# normalize_style_attrs() makes sure we can search for these patterns
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
    (re.compile(r"float:left*", re.IGNORECASE), transform_style_left),
    (re.compile(r"float:right*", re.IGNORECASE), transform_style_right),
]

TRANSFORM_TAGS_MAPPING = [
    ("strong", transform_tag_strong),
    ("em", transform_tag_em),
]

TRANSFORM_TAGS_ENABLED = getattr(
    settings, "WAGTAIL_WORDPRESS_IMPORT_TRANSFORM_TAGS_MAPPING_ENABLED", True
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
