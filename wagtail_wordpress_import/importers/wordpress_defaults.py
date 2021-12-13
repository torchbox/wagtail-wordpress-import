from django.conf import settings


def debug_enabled():
    return getattr(settings, "WAGTAIL_WORDPRESS_IMPORT_DEBUG_ENABLED", True)


def yoast_plugin_enabled():
    return getattr(settings, "WAGTAIL_WORDPRESS_IMPORT_YOAST_PLUGIN_ENABLED", False)


def yoast_plugin_config():
    """
    XML file fields
    <wp:postmeta>
        <wp:meta_key>_yoast_wpseo_metadesc</wp:meta_key>
        <wp:meta_value>a search description from yaost for Item two</wp:meta_value>
    </wp:postmeta>
    """
    return getattr(
        settings,
        "WAGTAIL_WORDPRESS_IMPORT_YOAST_PLUGIN_MAPPING",
        {
            "xml_item_key": "wp:postmeta",
            "description_key": "wp:meta_key",
            "description_value": "wp:meta_value",
            "description_key_value": "_yoast_wpseo_metadesc",
        },
    )


def category_plugin_enabled():
    return getattr(settings, "WAGTAIL_WORDPRESS_IMPORT_CATEGORY_PLUGIN_ENABLED", False)


def category_name_min_length():
    return getattr(
        settings, "WAGTAIL_WORDPRESS_IMPORT_CATEGORY_PLUGIN_MIN_NAME_LENGTH", 1
    )


def get_category_model():
    return getattr(settings, "WAGTAIL_WORDPRESS_IMPORT_CATEGORY_PLUGIN_MODEL", None)
