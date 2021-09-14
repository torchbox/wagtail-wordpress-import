from django.apps import AppConfig
from wagtail_xmlimport.importers import get_importers

class WagtailXmlimportImportersConfig(AppConfig):
    label = "wagtail_xmlimport_importers"
    name = "wagtail_xmlimport_importers"
    verbose_name = "Wagtail xmlimport importers"

    def ready(self):
        # check config on startup
        get_importers()