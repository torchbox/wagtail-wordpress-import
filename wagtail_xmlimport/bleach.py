from bs4 import BeautifulSoup as bs4
from wagtail_xmlimport.constants import *


from bleach.sanitizer import Cleaner


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


def fix_styles(value):
    """
    When encounting an inline style that is essitially to make the text
    bold, remove the style and tag and replace with a b tag
    """
    soup = bs4(value, "html.parser")
    search_styles = reverse_styles_dict(FILTER_MAPPING)

    for style_string in search_styles:
        filter = search_styles[style_string]

        for item in soup.find_all(style=style_string):
            # match FILTER_MAPPING keys
            # item is bs4 soup and can be manipulated
            # directly backk into the final returned soup

            try:
                item_type = HTML_TAGS[item.name]
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

    """edge cases"""
    for item in soup.find_all("center"):
        item.unwrap()

    for item in soup.find_all("em"):
        new_item = soup.new_tag("i")
        new_item.string = item.text
        item.replace_with(new_item)

    return str(soup)
