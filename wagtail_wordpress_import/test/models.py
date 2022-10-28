from django.db import models
from modelcluster.fields import ParentalManyToManyField
from wagtail import VERSION as WAGTAIL_VERSION

if WAGTAIL_VERSION >= (3, 0):
    from wagtail.admin.panels import FieldPanel
    from wagtail.fields import StreamField
    from wagtail.models import Page
else:
    from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
    from wagtail.core.fields import StreamField
    from wagtail.core.models import Page

from wagtail.snippets.models import register_snippet

from wagtail_wordpress_import.blocks import WPImportStreamBlocks
from wagtail_wordpress_import.models import WPImportedPageMixin


@register_snippet
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    panels = [FieldPanel("name")]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"


class TestPage(WPImportedPageMixin, Page):

    streamfield_kwargs = {"use_json_field": True} if WAGTAIL_VERSION >= (3, 0) else {}
    body = StreamField(WPImportStreamBlocks, **streamfield_kwargs)

    categories = ParentalManyToManyField(Category, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("body") if WAGTAIL_VERSION >= (3, 0) else StreamFieldPanel("body"),
    ]

    def import_wordpress_data(self, data):
        # wagtail page model fields
        self.title = data["title"]
        self.slug = data["slug"]
        self.first_published_at = data["first_published_at"]
        self.last_published_at = data["last_published_at"]
        self.latest_revision_created_at = data["latest_revision_created_at"]
        self.search_description = data["search_description"]

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
