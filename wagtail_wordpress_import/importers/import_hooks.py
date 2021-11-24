import copy

from django.conf import settings


class ItemsCache:
    """Store the WordPress XML item tags.
    These are items tags that don't represent a page in the XML file.
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

    def add_item_to_cache(self, hook, item):
        """Add an item dict to the cached hook if not already added"""
        hook = getattr(self, hook)
        item = copy.deepcopy(item)
        if "wp:postmeta" in item:  # wp:postmeta is not needed in the cache
            del item["wp:postmeta"]
        if item not in hook:
            hook.append(item)


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

    def add_item_to_cache(self, hook, item):
        """Add an item dict to the cached hook if not already added"""
        hook = getattr(self, hook)
        item = copy.deepcopy(item)
        if "wp:postmeta" in item:  # wp:postmeta is not needed in the cache
            del item["wp:postmeta"]
        if item not in hook:
            hook.append(item)
