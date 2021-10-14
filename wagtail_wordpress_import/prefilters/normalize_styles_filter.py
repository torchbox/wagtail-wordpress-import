from bs4 import BeautifulSoup


def filter_normalize_style_attrs(html, options=None):
    """
    There are different ways that styles are formatted coming out of wordpress.
    This mornalizes them so the know what the format is for later parsing.

    e.g. font-style: italic becomes font-style:italic;
    e.g. FONT-WEIGHT:400; becoms font-weight:400;

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
            el.attrs["style"] = " ".join(
                sorted(styles_list)
            )  # sorted seems like it might be useful later

    return str(soup)
