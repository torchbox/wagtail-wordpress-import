from django.db import models
from wagtail.admin.edit_handlers import FieldPanel, ObjectList, TabbedInterface
from wagtail.core.models import Page


class WPImportedPageMixin(Page):
    wp_post_id = models.IntegerField(blank=True, null=True)
    wp_post_type = models.CharField(max_length=255, blank=True, null=True)
    wp_link = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True

    wordpress_panels = [
        FieldPanel("wp_post_id"), 
        FieldPanel("wp_post_type"),
        FieldPanel("wp_link")
    ]

    edit_handler = TabbedInterface(
        [
            ObjectList(Page.content_panels, heading="Content"),
            ObjectList(Page.promote_panels, heading="Promote"),
            ObjectList(Page.settings_panels, heading="Settings", classname="settings"),
            ObjectList(wordpress_panels, heading="Wordpress Data"),
        ]
    )
