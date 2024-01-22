from django.conf import settings

def __append_or_set(tag, key, value):
    if tag.attrs.get(key):
        # The key class can be a string or list
        # so copy the mode that is being used currently
        # https://beautiful-soup-4.readthedocs.io/en/latest/index.html?highlight=find_all#multi-valued-attributes
        if type(tag.attrs[key]) is str:
            tag.attrs[key] += " " + value
        else:
            tag.attrs[key].append(value)
    else:
        tag.attrs[key] = value

def transform_style_bold(soup, tag):
    """
    Replace the input tag name with `b` and remove style attr
    """
    new_tag = soup.new_tag("b")
    new_tag.string = tag.text
    tag.replace_with(new_tag)


def transform_style_italic(soup, tag):
    """
    Replace the input tag name with `i` and remove style attr
    """
    new_tag = soup.new_tag("i")
    new_tag.string = tag.text
    tag.append(new_tag)


def transform_style_bold_italic(soup, tag):
    """
    Replace the input tag name with `b` and a child of `i` and remove style attr
    """
    new_b_tag = soup.new_tag("b")
    new_i_tag = soup.new_tag("i")
    new_i_tag.string = tag.text
    new_b_tag.append(new_i_tag)
    tag.replace_with(new_b_tag)


def transform_style_center(soup, tag):
    """
    apply a new css class to any existing classes
    """
    __append_or_set(tag, "class", "align-center")


def transform_style_left(soup, tag):
    """
    apply a new css class to any existing classes
    """
    __append_or_set(tag, "class", "align-left")


def transform_style_right(soup, tag):
    """
    apply a new css class to any existing classes
    """
    __append_or_set(tag, "class", "align-right")


def transform_float_left(soup, tag):
    """
    apply a new css class to any existing classes
    """
    __append_or_set(tag, "class", "float-left")


def transform_float_right(soup, tag):
    """
    apply a new css class to any existing classes
    """
    __append_or_set(tag, "class", "float-right")


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
