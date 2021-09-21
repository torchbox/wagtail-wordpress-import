from bs4 import BeautifulSoup as bs4

ALLOWED_TAGS = [
    "a",
    "abbr",
    "acronym",
    "aside",
    "b",
    "blockquote",
    "br",
    "button",
    "caption",
    "code",
    "col",
    "colgroup",
    "del",
    "div",
    "em",
    "footer",
    "form",
    "figure",
    "figcaption",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "iframe",
    "img",
    "input",
    "label",
    "li",
    "ol",
    "option",
    "p",
    "s",
    "script",
    "select",
    "small",
    "span",
    "strike",
    "strong",
    "style",
    "sup",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "time",
    "tr",
    "u",
    "ul",
    "wbr",
]

ALLOWED_ATTRIBUTES = {
    "*": ["class", "style", "id"],
    "a": [
        "aria-label",
        "data-wplink-edit",
        "href",
        "rel",
        "target",
        "title",
        "data-uw-rm-brl",
        "data-saferedirecturl",
        "name",
    ],
    "abbr": ["title"],
    "acronym": ["title"],
    "blockquote": [
        "data-cards",
        "data-lang",
        "data-instgrm-permalink",
        "data-instgrm-version",
        "data-instgrm-captioned",
    ],
    "button": ["data-target", "data-toggle"],
    "col": ["width"],
    "div": [
        "title",
        "data-campaign",
        "data-widget-id",
        "data-offer-id",
        "data-aff-id",
        "data-sub-id",
        "data-color",
        "role",
        "data-mm-rates",
    ],
    "form": ["action", "name", "method", "accept-charset"],
    "h2": ["big", "data-toctitle", "data-tocskip", "data-toskip", "data-toc-title"],
    "h3": ["data-toctitle", "data-tocskip"],
    "i": [
        "aria-hidden",
        "data-toggle",
        "data-placement",
        "title",
        "data-original-title",
    ],
    "iframe": [
        "allowfullscreen",
        "src",
        "width",
        "height",
        "frameborder",
        "scrolling",
        "marginwidth",
        "marginheight",
        "data-mce-fragment",
        "data-name",
        "data-link",
    ],
    "img": [
        "alt",
        "border",
        "data-src",
        "height",
        "sizes",
        "src",
        "srcset",
        "title",
        "width",
    ],
    "input": [
        "name",
        "placeholder",
        "readonly",
        "required",
        "type",
        "min",
        "max",
        "step",
        "value",
        "data-type",
    ],
    "label": ["for"],
    "li": ["aria-level", "value", "data-uw-node-idx"],
    "ol": ["data-mm-title", "start"],
    "option": ["data-desc", "data-option", "value", "selected"],
    "p": ["dir", "lang", "data-tocskip", "data-toctitle", "data-mm-rates"],
    "script": ["async", "charset", "defer", "src", "type"],
    "select": ["name"],
    "span": ["aria-invalid", "data-reactid", "data-preserver-spaces", "data-mm-rates"],
    "style": ["*"],
    "table": ["width", "dir", "border", "cellspacing", "cellpadding", "summary"],
    "tbody": ["data-mm-rates"],
    "td": [
        "data-label",
        "width",
        "colspan",
        "data-sheets-value",
        "data-sheets-numberformat",
        "data-sheets-formula",
        "data-sheets-hyperlink",
        "rowspan",
    ],
    "th": ["width", "scope", "colspan", "rowspan"],
    "time": ["datetime"],
    "ul": ["data-mm-title", "data-mm-rates"],
}

ALLOWED_STYLES = [
    # "border-top: 1px solid #E3DFD6; padding-top: 5px;",
    # "border: 1px solid #CCCCCC;",
    "color",
    # "float: left; margin: 0em 1em 1em 0em;",
    "font-size",
    # "font-size: 18px;",
    # "font-size:130%;",
    # "font-size:85%;",
    "font-weight",
    # "font-weight: bold;",
    "font-style: italic;",
    "font-style",
    # "height: 702px;",
    # "line-height: 2.0;",
    # "margin-bottom: -5px;",
    # "margin-left: 244px; margin-right: 25px;",
    # "margin-top: -10px;",
    # "margin-top: -10px; padding-top: 20px;",
    # "margin-top: -20px; margin-bottom: 0px;",
    # "margin-top: -5px;",
    # "margin-top: -5px; padding-bottom: 10px;",
    # "margin-top: -5px; padding-bottom: 15px;",
    # "margin-top: -5px; padding-bottom: 5px;",
    # "margin-top: -5px; padding-bottom: 5px; text-align: center;",
    # "margin-top: -8px;",
    # "margin-top: 25px;",
    # "margin-top: 30px;",
    # "margin-top: 5px;",
    # "margin-top:-5px; padding-bottom:5px;",
    # "margin: 0pt 10px 10px 0pt;float: none",
    # "padding-bottom: 10px;",
    # "padding-bottom: 15px;",
    # "padding-bottom: 15px; padding-top: 15px;",
    # "padding-bottom: 1px; padding-top: 25px;",
    # "padding-bottom: 20px",
    # "padding-bottom: 20px;",
    # "padding-bottom: 2px;",
    # "padding-bottom: 4px;",
    # "padding-bottom: 5px;",
    # "padding-bottom: 7px;",
    # "padding-left: 30px;",
    # "padding-top 25px; padding-bottom: 25px;",
    # "padding-top: 10px;",
    # "padding-top: 10px; padding-bottom: 10px;",
    # "padding-top: 10px; padding-bottom: 20px;",
    # "padding-top: 15px;",
    # "padding-top: 18px;",
    # "padding-top: 20px;",
    # "padding-top: 30px; padding-bottom: 30px;",
    # "padding-top: 5px; padding-bottom: 10px;",
    # "TEXT-ALIGN: center",
    # "text-align: center",
    # "text-align: center;",
    # "text-align: center; font-size: 16px;",
    # "text-align: center; margin-top: -10px;",
    # "text-align: center; margin-top: -10px; padding-bottom: 5px;",
    # "text-align: center; margin-top: -12px;",
    # "text-align: center; margin-top: 40px;",
    # "text-align: center; padding-bottom: 10px;",
    # "text-align: center; padding-bottom: 5px;",
    # "text-align: center; padding-top: 10px; padding-bottom: 10px;",
    # "text-align: center; padding-top: 15px;",
    # "text-align: center; padding-top: 15px; padding-bottom: 20px;",
    # "text-align: center; padding-top: 20px;",
    # "text-align: center; padding-top: 20px; padding-bottom: 20px;",
    # "text-align: center; padding-top: 30px;",
    # "text-align: left;",
    # "width: 560px; height: 220px;",
    # "width: 560px; padding: 8px; background: #EEEEEE; border: 2px solid gray; margin: 0px;",
]


from bleach.sanitizer import Cleaner
from bleach.html5lib_shim import Filter


def bleach_clean(value):
    """
    Clean up the raw html to be on the safe side.
    Keeping all styles in place that we know of and care about.
    See ALLOWED list above
    """

    cleaned = Cleaner(
        tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, styles=ALLOWED_STYLES
    )
    return cleaned.clean(value)


# Conveniant mapping of filters to selectors
INLINE_STYLES_TO_FIX = {
    # set the tag as b for all these font-weights
    "bold": {"styles": ["font-weight: bold;"], "tag": "b"},
    # unwrap when style attr exists because it means nothing as font-weight 400 is normal
    "unwrap": {"styles": ["font-weight: 400;"]},
    # remove
    "remove_tag": {"tags": ["span"]},
}


def boldify(value):
    """
    When encounting an inline style that is essitially to make the text
    bold, remove the style and tag and replace with a b tag
    """
    soup = bs4(value, "html.parser")
    search_styles = INLINE_STYLES_TO_FIX.get("bold")["styles"]
    new_tag = soup.new_tag(INLINE_STYLES_TO_FIX.get("bold")["tag"])

    for span in soup.findAll("span", attrs={"style": search_styles}):
        new_tag.string = span.text
        span.replace_with(new_tag)

    return str(soup)


def unwrapify(value):
    """
    When encountering a span tag that has style attributes that don't alter
    the display of the text e.g. font-weight: 400 then remove the enclosing tag
    """
    soup = bs4(value, "html.parser")
    search_styles = INLINE_STYLES_TO_FIX.get("unwrap")["styles"]

    for span in soup.findAll("span", attrs={"style": search_styles}):
        span.unwrap()

    return str(soup)


def removeify(value):
    """
    When encountering a tag e.g. span or div that has no attributes
    remove the enclosing tag
    """
    soup = bs4(value, "html.parser")
    tags = INLINE_STYLES_TO_FIX.get("remove_tag")["tags"]

    for i in range(len(tags)):
        for span in soup.findAll(tags[i]):
            if not span.attrs.values():
                span.unwrap()

    return str(soup)


def prettify(value):
    soup = bs4(value, "html.parser")
    return soup.prettify()
