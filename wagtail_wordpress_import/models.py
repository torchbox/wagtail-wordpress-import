from django.db import models
from wagtail.admin.edit_handlers import FieldPanel, FieldRowPanel
from wagtail.core.models import Page


class WPImportedPageMixin(Page):
    wp_post_id = models.IntegerField(blank=True, null=True)
    wp_post_type = models.CharField(max_length=255, blank=True, null=True)
    wp_link = models.TextField(blank=True, null=True)
    wp_raw_content = models.TextField(blank=True, null=True)
    wp_processed_content = models.TextField(blank=True, null=True)
    wp_block_json = models.TextField(blank=True, null=True)
    wp_normalized_styles = models.TextField(blank=True, null=True)
    wp_post_meta = models.JSONField(blank=True, null=True)

    class Meta:
        abstract = True

    def import_wordpress_data(self, data):
        raise NotImplementedError(
            "import_wordpress_data() method not implemented in your page model"
        )

    wordpress_panels = [
        FieldRowPanel(
            [
                FieldPanel("wp_post_id"),
                FieldPanel("wp_post_type"),
            ],
            heading="wp data",
        ),
        FieldPanel("wp_link", classname="full title"),
        FieldPanel("wp_block_json", classname="full"),
        FieldPanel("wp_processed_content", classname="full"),
        FieldPanel("wp_normalized_styles", classname="full"),
        FieldPanel("wp_raw_content", classname="full"),
        FieldPanel("wp_post_meta", classname="full"),
    ]
