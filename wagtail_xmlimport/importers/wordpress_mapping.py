mapping = {
    "root": {
        # The tag for each page in the xml file tree
        "tag": "item",
        # The page type in xml tag <wp:post_type>
        "type": "page",
        # The statuses to import
        "status": ["publish", "draft"],
    },
    "item": {
        "title": "title",
        # "description": "search_description",
        "wp:post_name": "slug",
        "wp:post_date_gmt": "first_published_at",
        "wp:post_modified_gmt": "last_published_at,latest_revision_created_at",
        "content:encoded": "body",
        "wp:post_id": "wp_post_id",
        "wp:post_type": "wp_post_type",
        "link": "wp_link",
    },
    "validate_date": "first_published_at,last_published_at,latest_revision_created_at",
    "validate_slug": "slug",
    "stream_fields": "body",
}
