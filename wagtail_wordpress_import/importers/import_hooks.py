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
        """Run all hooks in the config for each page
        The function defined in the config key FUNCTION will be imported
        and run on each page"""
        for page in imported_pages:
            func, data = self._get_hook_handler_data()
            import_string(func)(page, data, self.__dict__)

    def add_item_to_cache(self, hook, item):
        """Add an item dict to the cached hook if not already added"""
        hook = getattr(self, hook)
        if item not in hook:
            hook.append(item)

    def _get_hook_handler_data(self):
        """Get the hook function and data to process"""
        for hook, actions in getattr(
            settings, "WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE", {}
        ).items():
            if hook in self.__dict__:
                return actions["FUNCTION"], actions["DATA_TAG"]
        return None, None
