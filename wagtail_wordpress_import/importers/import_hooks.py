import copy

from django.conf import settings


class ItemsCache:
    """Store the WordPress XML item tags.
    These are item tags that don't represent a page in the XML file.
    They are temporarily stored and used at the end of the import process.
    """

    def __init__(self):
        """For each value in settings.WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE
        create the class attribute.
        """

        for hook in getattr(
            settings, "WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE", {}
        ).keys():
            setattr(self, hook, [])

    def add_item_to_cache(self, key, item):
        """Add an item dict to the list of cached items if not already added.

        key:
            The value from <wp:post_type>...</wp:post_type> of an item tag in the XML file.
        item:
            The complete item tag in the XML file as a dict.
        """

        cache = getattr(self, key)
        item = copy.deepcopy(item)
        if "wp:postmeta" in item:  # wp:postmeta is not needed in the cache
            del item["wp:postmeta"]
        if item not in cache:
            cache.append(item)


class TagsCache:
    """Store the WordPress XML top level tags.
    These are tags that don't represent a page in the XML file.
    They are temporarily stored and used at the end of the import process.
    """

    def __init__(self):
        """For each value in settings.WORDPRESS_IMPORT_HOOKS_TAGS_TO_CACHE
        create the class attribute.
        """

        for hook in getattr(settings, "WORDPRESS_IMPORT_HOOKS_TAGS_TO_CACHE", {}):
            setattr(self, hook, [])

    def add_item_to_cache(self, key, item):
        """Add an item dict to the list of cached items if not already added

        key:
            The XML tag name of a tag in the XML file.
        item:
            The complete tag in the XML file as a dict.
        """

        cache = getattr(self, key)
        item = copy.deepcopy(item)
        if "wp:postmeta" in item:  # wp:postmeta is not needed in the cache
            del item["wp:postmeta"]
        if item not in cache:
            cache.append(item)
