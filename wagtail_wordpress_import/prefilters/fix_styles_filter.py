from bs4 import BeautifulSoup as bs4
from django.utils.module_loading import import_string
from wagtail_wordpress_import.prefilters.constants import FILTER_MAPPING, HTML_TAGS


def reverse_styles_dict(mapping):
    inverse = {}

    for filter, styles in mapping.items():
        for style in styles:
            inverse[style] = filter
    """
    # note no ending `;` so we can split on it later
    {
        'FONT-WEIGHT: bold': 'boldify',
        'font-weight: bold': 'boldify',
        'font-weight: bold; color: #006600': 'boldify'
    }
    """
    return inverse


def filter_fix_styles(html, options=None):
    """
    This function uses the mapping of the style attribute for an element to break
    matching elements into one or more html tags.
    e.g. "font-weight: bold;" maps to "bold" - <b>text</b>
    e.g. "font-style: italic; font-weight: bold;" maps to "bold-italic" - <b><i>text</i></b>

    It also adds classes which are not directly used in the final content but interpreted
    later to decide if an element can have alignment in the richtext block
    e.g. "margin: 0pt 10px 0px 0pt; float: left;" maps to "leftfloat"
    e.g. "float: left; margin: 0em 1em 1em 0em;" maps to "leftfloat"

    param: `options` NOT IMPLEMENTED
    """

    if options and options["CONFIG"].get("HTML_TAGS"):
        # if options["CONFIG"].get("HTML_TAGS"):
        function = import_string(options["CONFIG"]["HTML_TAGS"])
        CONF_HTML_TAGS = function()
    else:
        CONF_HTML_TAGS = HTML_TAGS()

    if options and options["CONFIG"].get("FILTER_MAPPING"):
        function = import_string(options["CONFIG"]["FILTER_MAPPING"])
        CONF_FILTER_MAPPING = function()
    else:
        CONF_FILTER_MAPPING = FILTER_MAPPING()

    soup = bs4(html, "html.parser")
    search_styles = reverse_styles_dict(CONF_FILTER_MAPPING)

    for style_string in search_styles:
        filter = search_styles[style_string]

        for item in soup.find_all(style=style_string):
            # match FILTER_MAPPING keys
            # item is bs4 soup and can be manipulated
            # directly backk into the final returned soup

            try:
                item_type = CONF_HTML_TAGS[item.name]
            except KeyError:
                print("item.name = tag not found in HTML_TAGS")
                continue

            # REMOVE STYLE OR UNWRAP TEXT of e.g. span with useless style tag
            # best run first
            if item_type == "block" and filter == "remove":
                del item.attrs["style"]

            if item_type == "inline" and filter == "remove":
                item.unwrap()

            """run the inlines first"""

            # REPLACE TAG WITH <b>
            if item_type == "inline" and filter == "bold":
                new_tag = soup.new_tag("b")
                new_tag.string = item.text
                item.replace_with(new_tag)

            # REPLACE TAG WITH <i>
            if item_type == "inline" and filter == "italic":
                new_tag = soup.new_tag("i")
                new_tag.string = item.text
                item.replace_with(new_tag)

            # REPLACE TAG WITH <i> and <b>
            if item_type == "inline" and filter == "bold-italic":
                new_i_tag = soup.new_tag("i")
                new_i_tag.string = item.text
                new_b_tag = soup.new_tag("b")
                new_b_tag.append(new_i_tag)
                item.replace_with(new_b_tag)

            """and the blocks next"""
            # REPLACE TAG WITH <b>
            if item_type == "block" and filter == "bold":
                new_tag = soup.new_tag("b")
                new_tag.string = item.text
                item.replace_with(new_tag)

            # REPLACE TAG WITH <i>
            if item_type == "block" and filter == "italic":
                new_tag = soup.new_tag("i")
                new_tag.string = item.text
                item.replace_with(new_tag)

            # REPLACE TAG CHILDREN WITH <i> and <b> plus the text content
            if item_type == "block" and filter == "bold-italic":
                # create the whole new tag to replace the item completely
                new_b_tag = soup.new_tag("b")
                new_i_tag = soup.new_tag("i")
                new_i_tag.string = item.text
                new_b_tag.append(new_i_tag)
                new_item_tag = soup.new_tag(item.name)  # a new item tag
                new_item_tag.append(new_b_tag)
                item.replace_with(new_item_tag)

            """add classes"""
            # ALIGN CENTER by adding class="align-center"
            if filter == "center":
                del item.attrs["style"]
                item.attrs["class"] = "align-center"

            # FLOAT LEFT by adding class="align-left"
            if filter == "leftfloat":
                del item.attrs["style"]
                item.attrs["class"] = "align-left"

            # FLOAT RIGH by adding class="float-right"
            if filter == "rightfloat":
                del item.attrs["style"]
                item.attrs["class"] = "align-right"

    """other cases"""
    for item in soup.find_all("center"):
        item.unwrap()

    for item in soup.find_all("em"):
        new_item = soup.new_tag("i")
        new_item.string = item.text
        item.replace_with(new_item)

    for item in soup.find_all("strong"):
        new_item = soup.new_tag("b")
        new_item.string = item.text
        item.replace_with(new_item)

    fixed_html = str(soup)

    return fixed_html
