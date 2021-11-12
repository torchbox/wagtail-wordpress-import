from django.conf import settings


def import_hooks_xml_tags_to_cache():
    """the xml top level tags to cache until the import process ends"""
    return getattr(settings, "WORDPRESS_IMPORT_HOOKS_TAGS_TO_CACHE", [])


class TagsCache:
    """a place to store the WordPress XML top level tags"""

    def __init__(self):
        """based on the values in settings.WORDPRESS_IMPORT_HOOKS_TAGS_TO_CACHE
        create the class attributes

        Each class attribute is a list.
        If one of the config items has a name of "wp:author" a class attribute
        author = [] will be created
        'wp:' is removed from the name to make it suitable for use a attribute name

        During the import process all "wp:author" tags would be parsed as a dict
        and stored in the author attribute.
        """

        for hook in import_hooks_xml_tags_to_cache():
            setattr(self, get_hook_name(hook), [])


def get_hook_name(hook):
    return hook.replace("wp:", "")


# def init_tags_cache():
#     tags_cache = TagsCache()
#     # initialise the tags_cache
#     for hook in conf_hooks_persist_xml_tags():
#         setattr(tags_cache, get_hook_name(hook), [])
#     return tags_cache


# def conf_hooks_persist_xml_items():
#     """configuration for the xml items tags to persist that have a specific post_type"""
#     return getattr(settings, "WORDPRESS_IMPORT_HOOKS_PERSIST_ITEMS", [])
