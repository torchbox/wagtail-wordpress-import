mapping = {
    "root": {
        "//[ The tag for each page in the xml file tree ]//": "",
        "tag": "item",
        "//[ The page type in xml tag <wp:post_type> ]//": "",
        "type": "page",
        "//[ The statuses to import ]//": "",
        "status": ["publish", "draft"],
    },
    "item": {
        "title": "title",
        "content:encoded": "body",
        "wp:post_id": "wp_post_id",
        "wp:post_name": "slug",
        "wp:post_date_gmt": "first_published_at",
        "wp:post_modified_gmt": [
            "last_published_at", "latest_revision_created_at",
        ],
    },
}
