from django.db import models
from wagtail.core.models import Page

from wagtail_wordpress_import.models import WPImportedPageMixin
from wagtail.core.fields import StreamField
from wagtail.admin.edit_handlers import StreamFieldPanel
from wagtail_wordpress_import.blocks import WPImportStreamBlocks


class TestPage(WPImportedPageMixin, Page):
    body = StreamField(WPImportStreamBlocks)

    content_panels = Page.content_panels + [
        StreamFieldPanel("body"),
    ]

    def import_wordpress_data(self, data):
        # wagtail page model fields
        self.title = data["title"]
        self.slug = data["slug"]
        self.first_published_at = data["first_published_at"]
        self.last_published_at = data["last_published_at"]
        self.latest_revision_created_at = data["latest_revision_created_at"]

        # debug fields
        self.wp_post_id = data["wp_post_id"]
        self.wp_post_type = data["wp_post_type"]
        self.wp_link = data["wp_link"]
        self.wp_raw_content = data["wp_raw_content"]
        self.wp_block_json = data["wp_block_json"]
        self.wp_processed_content = data["wp_processed_content"]
        self.wp_normalized_styles = data["wp_normalized_styles"]

        # own model fields
        self.body = data["body"]
