from bleach.sanitizer import Cleaner
from wagtail_wordpress_import.constants import (
    ALLOWED_ATTRIBUTES,
    ALLOWED_STYLES,
    ALLOWED_TAGS,
)


def filter_bleach_clean(html, options=None):
    """
    Clean up the raw html to be on the safe side.
    Keeping all styles in place that we know of and care about.
    See ALLOWED lists in wagtail-wordpress-import/wagtail_wordpress_import/constants.py
    """

    cleaned = Cleaner(
        tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, styles=ALLOWED_STYLES
    )

    cleaned_html = cleaned.clean(html)
    return cleaned_html
