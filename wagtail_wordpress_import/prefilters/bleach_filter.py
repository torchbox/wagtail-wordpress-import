from bleach.sanitizer import Cleaner
from django.utils.module_loading import import_string
from wagtail_wordpress_import.prefilters.constants import (
    ALLOWED_ATTRIBUTES,
    ALLOWED_STYLES,
    ALLOWED_TAGS,
)  #


def filter_bleach_clean(html, options=None):
    """
    We do a final clean up on the processed html to be on the safe side
    as part of the default filters.

    See ALLOWED lists in wagtail_wordpress_import/prefilters/constants.py

    You can disable this filter in your app settings WAGTAIL_WORDPRESS_IMPORT_PREFILTERS
    Copy the default filters from wagtail_wordpress_import/importers/wordpress.py DEFAULT_FILTERS
    and remove `wagtail_wordpress_import.prefilters.bleach_filter.filter_bleach_clean` filter
    """

    CONF_ALLOWED_TAGS = ALLOWED_TAGS
    if options and options.get("ADDITIONAL_ALLOWED_TAGS"):
        allowed_tags = import_string(options["ADDITIONAL_ALLOWED_TAGS"])
        if callable(allowed_tags):
            CONF_ALLOWED_TAGS = allowed_tags()
        else:
            CONF_ALLOWED_TAGS = CONF_ALLOWED_TAGS + options["ADDITIONAL_ALLOWED_TAGS"]

    CONF_ALLOWED_ATTRIBUTES = ALLOWED_ATTRIBUTES
    if options and options.get("ADDITIONAL_ALLOWED_ATTRIBUTES"):
        allowed_attributes = import_string(options["ADDITIONAL_ALLOWED_ATTRIBUTES"])
        if callable(allowed_attributes):
            CONF_ALLOWED_ATTRIBUTES = allowed_attributes()
        else:
            CONF_ALLOWED_ATTRIBUTES = (
                CONF_ALLOWED_ATTRIBUTES + options["ADDITIONAL_ALLOWED_ATTRIBUTES"]
            )

    CONF_ALLOWED_STYLES = ALLOWED_STYLES
    if options and options.get("ADDITIONAL_ALLOWED_STYLES"):
        allowed_styles = import_string(options["ADDITIONAL_ALLOWED_STYLES"])
        if callable(allowed_styles):
            CONF_ALLOWED_STYLES = allowed_styles()
        else:
            CONF_ALLOWED_STYLES = (
                CONF_ALLOWED_STYLES + options["ADDITIONAL_ALLOWED_STYLES"]
            )

    cleaned = Cleaner(
        tags=CONF_ALLOWED_TAGS,
        attributes=CONF_ALLOWED_ATTRIBUTES,
        styles=CONF_ALLOWED_STYLES,
    )

    cleaned_html = cleaned.clean(html)
    return cleaned_html
