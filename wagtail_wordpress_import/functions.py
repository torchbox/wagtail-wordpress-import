from collections import defaultdict

from bs4 import BeautifulSoup
from bs4.element import Stylesheet


def clean_node_name(node_name):
    return node_name.replace("-", "_")


def coerce_node_value(value):
    if value.isnumeric():
        return int(value)
    if value == "true":
        return True
    if value == "false":
        return False
    return value


def get_node_value(node):
    if len(node.childNodes) == 0:
        return node.nodeName, None
    else:
        contains_element_node = False
        for child_node in node.childNodes:
            if child_node.nodeType == node.ELEMENT_NODE:
                contains_element_node = True
                break
        if contains_element_node:
            return node.nodeName, node_to_dict(node)
        else:
            return node.nodeName, coerce_node_value(
                "".join(child_node.nodeValue for child_node in node.childNodes)
            )


def node_to_dict(node):
    obj = defaultdict(list)
    for child_node in node.childNodes:
        if child_node.nodeType == node.ELEMENT_NODE:
            name, value = get_node_value(child_node)
            obj[clean_node_name(name)].append(value)
        elif child_node.nodeType == node.TEXT_NODE:
            pass  # Usually whitespace
        else:
            raise Exception()
    # If an element appears more than once, use an array.
    # Otherwise just use the element value.
    obj = {key: value[0] if len(value) == 1 else value for key, value in obj.items()}
    if obj == {"nil": True}:
        return None
    return obj


import re
from django.utils.html import escape
from django.utils.text import normalize_newlines


def linebreaks_wp(pee, autoescape=False):
    """
    Straight up port of http://codex.wordpress.org/Function_Reference/wpautop
    i am greatful https://gist.github.com/albertsun/1160201
    """
    # print(pee)
    # seeing an error here when the first charcter is a int
    # if (pee.strip() == ""):
    #     return ""
    pee = normalize_newlines(pee)
    pee = pee + "\n"
    pee = re.sub(r"<br />\s*<br />", "\n\n", pee)
    allblocks = r"(?:table|thead|tfoot|caption|col|colgroup|tbody|tr|td|th|div|dl|dd|dt|ul|ol|li|pre|select|option|form|map|area|blockquote|address|math|style|input|p|h[1-6]|hr|fieldset|legend|section|article|aside|hgroup|header|footer|nav|figure|figcaption|details|menu|summary)"
    pee = re.sub(
        r"(<" + allblocks + "[^>]*>)",
        lambda m: "\n" + m.group(1) if m.group(1) else "\n",
        pee,
    )
    pee = re.sub(
        r"(</" + allblocks + ">)",
        lambda m: m.group(1) + "\n\n" if m.group(1) else "\n\n",
        pee,
    )
    # pee = pee.replace("\r\n", "\n")
    # pee = pee.replace("\r", "\n") #these taken care of by normalize_newlines
    if pee.find("<object") != -1:
        pee = re.sub(
            r"\s*<param([^>]*)>\s*",
            lambda m: "<param%s>" % (m.group(1) if m.group(1) else "",),
            pee,
        )  # no pee inside object/embed
        pee = re.sub(r"\s*</embed>\s*", "</embed>", pee)
    pee = re.sub(r"\n\n+", "\n\n", pee)  # take care of duplicates
    pees = re.split(
        r"\n\s*\n", pee
    )  # since PHP has a PREG_SPLIT_NO_EMPTY, may need to go through and drop any empty strings
    # pees = [p for p in pees if p]
    pee = "".join(["<p>%s</p>\n" % tinkle.strip("\n") for tinkle in pees])
    pee = re.sub(
        r"<p>\s*</p>", "", pee
    )  # under certain strange conditions it could create a P of entirely whitespace
    pee = re.sub(
        r"<p>([^<]+)</(div|address|form)>",
        lambda m: "<p>%s</p></%s>"
        % (
            (lambda x: x.group(1) if x.group(1) else "")(m),
            (lambda x: x.group(2) if x.group(2) else "")(m),
        ),
        pee,
    )
    pee = re.sub(
        r"<p>\s*(</?" + allblocks + r"[^>]*>)\s*</p>",
        lambda m: m.group(1) if m.group(1) else "",
        pee,
    )  # don't pee all over a tag
    pee = re.sub(
        r"<p>(<li.+?)</p>", lambda m: m.group(1) if m.group(1) else "", pee
    )  # problem with nested lists
    pee = re.sub(
        r"<p><blockquote([^>]*)>",
        # lambda m: "<blockquote%s><p>" % (m.group(1) if m.group(1) else "",),
        # found this not to our liking as it puts a p tag around the blockquote content
        lambda m: "<blockquote%s>" % (m.group(1) if m.group(1) else "",),
        pee,
        flags=re.IGNORECASE,
    )
    # pee = pee.replace("</blockquote></p>", "</p></blockquote>")
    # found this not to our liking as it puts a p tag around the blockquote content
    pee = pee.replace("</blockquote></p>", "</blockquote>")
    pee = re.sub(
        r"<p>\s*(</?" + allblocks + r"[^>]*>)",
        lambda m: m.group(1) if m.group(1) else "",
        pee,
    )
    pee = re.sub(
        r"(</?" + allblocks + "[^>]*>)\s*</p>",
        lambda m: m.group(1) if m.group(1) else "",
        pee,
    )

    def _autop_newline_preservation_helper(matches):
        return matches.group(0).replace("\n", "<WPPreserveNewline />")

    pee = re.sub(
        r"<(script|style).*?</\1>",
        _autop_newline_preservation_helper,
        pee,
        flags=re.DOTALL,
    )
    pee = re.sub(r"(?<!<br />)\s*\n", "<br />\n", pee)  # make line breaks
    pee = pee.replace("<WPPreserveNewline />", "\n")

    pee = re.sub(
        r"(</?" + allblocks + "[^>]*>)\s*<br />",
        lambda m: m.group(1) if m.group(1) else "",
        pee,
    )
    pee = re.sub(
        r"<br />(\s*</?(?:p|li|div|dl|dd|dt|th|pre|td|ul|ol)[^>]*>)",
        lambda m: m.group(1) if m.group(1) else "",
        pee,
    )
    if pee.find("<pre") != -1:

        def clean_pre(m):
            if m.group(1) and m.group(2):
                text = m.group(2)
                text = text.replace("<br />", "")
                text = text.replace("<p>", "\n")
                text = text.replace("</p>", "")
                text = m.group(1) + escape(text) + "</pre>"
            else:
                text = m.group(0)
                text = text.replace("<br />", "")
                text = text.replace("<p>", "\n")
                text = text.replace("</p>", "")

            return text

        pee = re.sub("(?is)(<pre[^>]*>)(.*?)</pre>", clean_pre, pee)
    pee = re.sub(r"\n</p>$", "</p>", pee)
    return pee


def normalize_style_attrs(html):
    """
    There are different ways that styles are formatted coming out of wordpress.
    This mornalizes them so the know what the format is for later parsing.

    e.g. font-style: italic becomes font-style:italic;
    e.g. FONT-WEIGHT:400; becoms font-weight:400;

    So essentially the styles are all lowercased, with appended ; and have no spaces.
    Worth noting that these styles are actually removed later on when the fix_styles
    method is run so if they look wrong it's OK here as they are a `template`
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
            el.attrs["style"] = " ".join(
                sorted(styles_list)
            )  # sorted seems like it might be useful later

    return str(soup)
