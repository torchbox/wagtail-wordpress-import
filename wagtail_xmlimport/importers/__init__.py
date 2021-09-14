from importlib import import_module
from django.conf import settings
from django.utils.module_loading import import_string


def import_importer_class(dotted_path):
    """
    Imports a importer class from a dotted path. If the dotted path points to a
    module, that module is imported and its "wagtail_xmlimport_importer_class" class returned.
    If not, this will assume the dotted path points to directly a class and
    will attempt to import that instead.
    """
    try:
        importer_module = import_module(dotted_path)
        print(import_module)
        return importer_module.wordpress_importer_class
    except ImportError as e:
        try:
            return import_string(dotted_path)
        except ImportError:
            raise ImportError from e


def _get_config_from_settings():
    if hasattr(settings, "WAGTAIL_XML_BULK_IMPORTERS"):
        return settings.WAGTAIL_XML_BULK_IMPORTERS
    else:
        # Default to the oembed backend
        return [
            {
                "class": "wagtail_xmlimport.importers.wordpress",
            }
        ]


def get_importers():
    importers = []

    for importer_config in _get_config_from_settings():
        importer_config = importer_config.copy()
        cls = import_importer_class(importer_config.pop("class"))

        importers.append(cls(**importer_config))

    return importers
