from bleach.sanitizer import Cleaner

from wagtail_wordpress_import.prefilters.handle_shortcodes import SHORTCODE_HANDLERS


def filter_bleach_clean(html, options=None):
    """
    We do a final clean up on the processed html to be on the safe side.
    """

    CONF_ALLOWED_TAGS = ALLOWED_TAGS
    if options and options.get("ADDITIONAL_ALLOWED_TAGS"):
        CONF_ALLOWED_TAGS += options["ADDITIONAL_ALLOWED_TAGS"]

    # Registered shortcode handlers generate custom tags
    # so they need to be added to ALLOWED_TAGS

    for handler in SHORTCODE_HANDLERS:
        if handler.is_top_level_html_tag:
            CONF_ALLOWED_TAGS.append(handler().element_name)

    CONF_ALLOWED_ATTRIBUTES = ALLOWED_ATTRIBUTES
    if options and options.get("ADDITIONAL_ALLOWED_ATTRIBUTES"):
        CONF_ALLOWED_ATTRIBUTES.update(options["ADDITIONAL_ALLOWED_ATTRIBUTES"])

    CONF_ALLOWED_STYLES = ALLOWED_STYLES
    if options and options.get("ADDITIONAL_ALLOWED_STYLES"):
        CONF_ALLOWED_STYLES += options["ADDITIONAL_ALLOWED_STYLES"]

    cleaned = Cleaner(
        tags=CONF_ALLOWED_TAGS,
        attributes=CONF_ALLOWED_ATTRIBUTES,
        styles=CONF_ALLOWED_STYLES,
    )

    cleaned_html = cleaned.clean(html)
    return cleaned_html


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
    "center",  # not stictly allowed but we convert id later to css on a div
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
    "*": ["id"],
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
    "span": [
        "aria-invalid",
        "data-reactid",
        "data-preserver-spaces",
        "data-mm-rates",
    ],
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
    "font-size",
    "font-weight",
    "font-style: italic;",
    "font-style",
    "text-align: center",
    "text-align: center;",
]
