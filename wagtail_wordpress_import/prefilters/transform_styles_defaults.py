import re
from django.conf import settings


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
    if tag.attrs.get("class"):
        tag.attrs["class"].append("align-center")
    else:
        tag.attrs["class"] = "align-center"


def transform_style_left(soup, tag):
    """
    apply a new css class to any existing classes
    """
    if tag.attrs.get("class"):
        tag.attrs["class"].append("align-left")
    else:
        tag.attrs["class"] = "align-left"


def transform_style_right(soup, tag):
    """
    apply a new css class to any existing classes
    """
    if tag.attrs.get("class"):
        tag.attrs["class"].append("align-right")
    else:
        tag.attrs["class"] = "align-right"


def transform_float_left(soup, tag):
    """
    apply a new css class to any existing classes
    """
    if tag.attrs.get("class"):
        tag.attrs["class"].append("float-left")
    else:
        tag.attrs["class"] = "float-left"


def transform_float_right(soup, tag):
    """
    apply a new css class to any existing classes
    """
    if tag.attrs.get("class"):
        tag.attrs["class"].append("float-right")
    else:
        tag.attrs["class"] = "float-right"


def conf_styles_mapping():
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
    return getattr(
        settings,
        "WAGTAIL_WORDPRESS_IMPORT_PREFILTERS",
        [
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
        ],
    )


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


def conf_transform_html_tags_mapping():
    """
    It's intended that a developer can override this configuration and provide their own tag rules

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
    return getattr(
        settings,
        "WAGTAIL_WORDPRESS_IMPORT_TRANSFORM_HTML_TAGS_MAPPING",
        [
            ("strong", transform_html_tag_strong),
            ("em", transform_html_tag_em),
        ],
    )


def conf_transform_html_tags_enabled():
    """
    In your own settings you can disable the transformation of HTML tags using

    WAGTAIL_WORDPRESS_IMPORT_TRANSFORM_HTML_TAGS_ENABLED = False
    """
    return getattr(
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
