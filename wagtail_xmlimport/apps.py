from django.apps import AppConfig
# from wagtail_xmlimport.importers import get_importers
class WagtailXmlimportAppConfig(AppConfig):
    label = "wagtail_xmlimport"
    name = "wagtail_xmlimport"
    verbose_name = "Wagtail xmlimport"

    # def ready(self):
    #     # check config on startup
    #     get_importers()