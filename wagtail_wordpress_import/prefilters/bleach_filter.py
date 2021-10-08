from bleach.sanitizer import Cleaner
from wagtail_wordpress_import.prefilters.constants import (
    ALLOWED_ATTRIBUTES,
    ALLOWED_STYLES,
    ALLOWED_TAGS,
)


def filter_bleach_clean(html, options=None):
    """
    We do a final clean up on the processed html to be on the safe side
    as part of the default filters.

    See ALLOWED lists in wagtail_wordpress_import/prefilters/constants.py

    You can disable this filter in your app settings WAGTAIL_WORDPRESS_IMPORT_PREFILTERS
    Copy the default filters from wagtail_wordpress_import/importers/wordpress.py DEFAULT_FILTERS
    and remove `wagtail_wordpress_import.prefilters.bleach_filter.filter_bleach_clean` filter
    """

    allowed_tags = ALLOWED_TAGS()
    allowed_attributes = ALLOWED_ATTRIBUTES()
    allowed_styles = ALLOWED_STYLES()

    if options:
        if options.get("ADDITIONAL_ALLOWED_TAGS"):
            allowed_tags = ALLOWED_TAGS() + options["ADDITIONAL_ALLOWED_TAGS"]

        if options.get("ADDITIONAL_ALLOWED_ATTRIBUTES"):
            allowed_attributes = (
                ALLOWED_ATTRIBUTES() + options["ADDITIONAL_ALLOWED_ATTRIBUTES"]
            )

        if options.get("ADDITIONAL_ALLOWED_STYLES"):
            allowed_styles = ALLOWED_STYLES() + options["ADDITIONAL_ALLOWED_STYLES"]

    cleaned = Cleaner(
        tags=allowed_tags, attributes=allowed_attributes, styles=allowed_styles
    )

    cleaned_html = cleaned.clean(html)
    return cleaned_html
