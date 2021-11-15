from django.conf import settings


def import_hooks_xml_items_to_cache():
    """the xml item tags to cache until the import process ends"""
    return getattr(settings, "WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE", {})


class ItemsCache:
    """a place to store the WordPress XML item tags
    These are items tags the don't represent a page to be importred.
    For example: Images are represented by an <item> tag with a specific
    <wp:post_type>attachment</wp:post_type>"""

    def __init__(self):
        """based on the values in settings.WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE
        create the class attributes

        Each class attribute is a list.
        If one of the config items has a name of "attachment" a class attribute
        attachment = [] will be created

        During the import process all
        <item>
        ...
            <wp:post_type>attachment</wp:post_type>
        ...
        </item>
        tags would be parsed as a dict and stored in the attachment attribute.
        """

        for hook in import_hooks_xml_items_to_cache():
            setattr(self, hook, [])
