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
        """

        for hook in getattr(
            settings, "WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE", {}
        ).keys():
            setattr(self, hook, [])

    def process(self, imported_pages):
        """Run all hooks in the config for each page.

        Each function defined in the config key "FUNCTION" will be run on each page.
        """
        registry = self._get_hook_handler_data()
        for page in imported_pages:
            for hook, (func, data_tag) in registry.items():
                func(page, data_tag, self.__dict__)

    def add_item_to_cache(self, hook, item):
        """Add an item dict to the cached hook if not already added"""
        hook = getattr(self, hook)
        if item not in hook:
            hook.append(item)

    def _get_hook_handler_data(self):
        """Get the hook functions and data_tag names to process."""
        return {
            hook: (import_string(actions["FUNCTION"]), actions["DATA_TAG"])
            for hook, actions in getattr(
                settings, "WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE", {}
            ).items()
            if hook in self.__dict__
        }
