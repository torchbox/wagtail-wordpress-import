from django.conf import settings


def build_block_quote_block(tag):
    block_dict = {
        "type": "block_quote",
        "value": {"quote": tag.text.strip(), "attribution": tag.cite},
    }
    return block_dict


def build_form_block(tag):
    block_dict = {"type": "raw_html", "value": str(tag)}
    return block_dict


def build_heading_block(tag):
    block_dict = {
        "type": "heading",
        "value": {"importance": tag.name, "text": tag.text},
    }
    return block_dict


def build_iframe_block(tag):
    block_dict = {
        "type": "raw_html",
        "value": '<div class="core-custom"><div class="responsive-iframe">{}</div></div>'.format(
            str(tag)
        ),
    }
    return block_dict


def build_image_block(tag):
    def get_image_id(src):
        return 1

    block_dict = {"type": "image", "value": get_image_id(tag.src)}
    return block_dict


def build_table_block(tag):
    block_dict = {"type": "raw_html", "value": str(tag)}
    return block_dict


def conf_html_tags_to_blocks():
    return getattr(
        settings,
        "WAGTAIL_WORDPRESS_IMPORTER_CONVERT_HTML_TAGS_TO_BLOCKS",
        [
            (
                "h1",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
                },
            ),
            (
                "h2",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
                },
            ),
            (
                "h3",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
                },
            ),
            (
                "h4",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
                },
            ),
            (
                "h5",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
                },
            ),
            (
                "h6",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
                },
            ),
            (
                "table",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_table_block",
                },
            ),
            (
                "iframe",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_iframe_block",
                },
            ),
            (
                "form",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_form_block",
                },
            ),
            (
                "img",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_image_block",
                },
            ),
            (
                "blockquote",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_block_quote_block",
                },
            ),
        ],
    )


def conf_fallback_block():
    return getattr(
        settings,
        "WAGTAIL_WORDPRESS_IMPORTER_FALLBACK_BLOCK",
        "wagtail_wordpress_import.block_builder_defaults.build_none_block_content",
    )


def build_none_block_content(cache, blocks):
    blocks.append({"type": "rich_text", "value": cache})
    cache = ""
    return cache
