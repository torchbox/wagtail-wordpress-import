from django.conf import settings
from django.utils.module_loading import import_string


class ItemsCache:
    """Store the WordPress XML item tags.
    These are items tags that don't represent a page in the XML file.
    They are temporarily stored and used at the end of the import process.
    """

    def __init__(self):
        """For each value in settings.WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE
        create the class attribute.

        For example:
        If a config item has a key of "attachment" a class attribute
        attachment: list would be created

        XML fragment example:
        <item>
            <title>foo-item</title>
            <link>https://www.example.com/foo-item/</link>
            <pubDate>Tue, 13 Jul 2010 16:16:46 +0000</pubDate>
            <guid>https://www.example.com/foo.jpg</guid>
            <wp:post_id>100</wp:post_id>
            <wp:post_date>2010-07-13 12:16:46</wp:post_date>
            <wp:post_date_gmt>2010-07-13 16:16:46</wp:post_date_gmt>
            <wp:post_modified>2010-07-13 16:16:46</wp:post_modified>
            <wp:post_modified_gmt>2010-07-13 16:16:46</wp:post_modified_gmt>
            <wp:post_name>foo-item</wp:post_name>
            <wp:post_type>attachment</wp:post_type>
        </item>
        would be parsed as a dict
        {
            "title": "foo-item",
            "link": "https://www.example.com/foo-item/",
            "pubDate": "Tue, 13 Jul 2010 16:16:46 +0000",
            "guid": "https://www.example.com/foo.jpg",
            "wp:post_id": 100,
            "wp:post_date": "2010-07-13 12:16:46",
            "wp:post_date_gmt": "2010-07-13 16:16:46",
            "wp:post_modified": "2010-07-13 12:16:46",
            "wp:post_modified_gmt": "2010-07-13 16:16:46",
            "wp:post_name": "foo-item",
            "wp:post_type": "attachment",
        }
        and stored in the attachment attribute.
        """

        for hook in getattr(settings, "WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE", {}):
            setattr(self, hook, [])

    def get_cached_items(self):
        """Return all the cached attributes added from the current config"""
        return self.__dict__

    def process(self, imported_pages, items_cache):
        """Run all hooks in the config for each page
        The function defined in the config key FUNCTION will be imported
        and run on each page"""
        for page in imported_pages:
            for hook in getattr(settings, "WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE", {}):
                func, data = self._get_hook_handler_data(items_cache)
                import_string(func)(page, data, items_cache)

    @staticmethod
    def _get_hook_handler_data(items_cache):
        """Get the hook function and data to process"""
        for hook, actions in getattr(
            settings, "WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE", {}
        ).items():
            if hook in items_cache:
                return actions["FUNCTION"], actions["DATA_TAG"]
        return None, None
