import json
from datetime import datetime
from functools import cached_property
from xml.dom import pulldom

from django.apps import apps
from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.text import slugify
from django.utils.timezone import make_aware
from wagtail.core.models import Page
from wagtail_wordpress_import.block_builder import BlockBuilder
from wagtail_wordpress_import.functions import node_to_dict
from wagtail_wordpress_import.prefilters.linebreaks_wp_filter import (
    filter_linebreaks_wp,
)


class WordpressImporter:
    def __init__(self, xml_file_path):
        self.xml_file = xml_file_path

    def run(self, *args, **kwargs):
        logger = kwargs["logger"]
        xml_doc = pulldom.parse(self.xml_file)

        try:
            self.page_model_instance = apps.get_model(
                kwargs["app_for_pages"], kwargs["model_for_pages"]
            )
        except LookupError:
            print(
                f"The app `{kwargs['app_for_pages']}` and/or page model `{kwargs['model_for_pages']}` cannot be found!"
            )
            print(
                "Check the command line options -a and -m match an existing Wagtail app and Wagtail page model"
            )
            exit()

        try:
            self.parent_page_obj = Page.objects.get(pk=kwargs["parent_id"])
        except Page.DoesNotExist:
            print(f"A page with id {kwargs['parent_id']} does not exist")
            exit()

        for event, node in xml_doc:
            # each node represents a tag in the xml
            # event is true for the start element
            if event == pulldom.START_ELEMENT and node.tagName == "item":
                xml_doc.expandNode(node)
                item = node_to_dict(node)
                logger.processed += 1

                if (
                    item.get("wp:post_type") in kwargs["page_types"]
                    and item.get("wp:status") in kwargs["page_statuses"]
                ):

                    wordpress_item = WordpressItem(item, logger)

                    try:
                        page = self.page_model_instance.objects.get(
                            wp_post_id=wordpress_item.cleaned_data.get("wp_post_id")
                        )
                    except self.page_model_instance.DoesNotExist:
                        page = self.page_model_instance()

                    page.import_wordpress_data(wordpress_item.cleaned_data)

                    if item.get("wp:status") == "draft":
                        setattr(page, "live", False)
                    else:
                        setattr(page, "live", True)

                    if page.id:
                        page.save()
                        logger.imported += 1
                        logger.items.append(
                            {
                                "id": page.id,
                                "title": page.title,
                                "link": item.get("link"),
                                "result": "updated",
                                "reason": "existed",
                                "datecheck": wordpress_item.date_changed,
                                "slugcheck": wordpress_item.slug_changed,
                            }
                        )
                    else:
                        self.parent_page_obj.add_child(instance=page)
                        page.save()
                        logger.imported += 1
                        logger.items.append(
                            {
                                "id": page.id,
                                "title": page.title,
                                "link": item.get("link"),
                                "result": "updated",
                                "reason": "existed",
                                "datecheck": wordpress_item.date_changed,
                                "slugcheck": wordpress_item.slug_changed,
                            }
                        )
                else:
                    logger.skipped += 1
                    logger.items.append(
                        {
                            "id": 0,
                            "title": "",
                            "link": "",
                            "result": "excluded",
                            "reason": "not a page type or status to import",
                            "datecheck": "",
                            "slugcheck": "",
                        }
                    )
            else:
                logger.items.append(
                    {
                        "id": 0,
                        "title": "",
                        "link": "",
                        "result": "excluded",
                        "reason": "not a item",
                        "datecheck": "",
                        "slugcheck": "",
                    }
                )
            logger.log_progress()

    def analyze_html(self, html_analyzer, *, page_types, page_statuses):
        xml_doc = pulldom.parse(self.xml_file)

        for event, node in xml_doc:
            # each node represents a tag in the xml
            # event is true for the start element
            if event == pulldom.START_ELEMENT and node.tagName == "item":
                xml_doc.expandNode(node)
                item = node_to_dict(node)
                if (
                    item.get("wp:post_type") in page_types
                    and item.get("wp:status") in page_statuses
                ):

                    html_analyzer.analyze(
                        filter_linebreaks_wp(item.get("content:encoded"))
                    )


DEFAULT_PREFILTERS = [
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.linebreaks_wp",
    },
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.transform_inline_styles_to_tags",
    },
    {
        "FUNCTION": "wagtail_wordpress_import.prefilters.bleach_clean",
    },
]

DEBUG_ENABLED = getattr(settings, "WAGTAIL_WORDPRESS_IMPORT_DEBUG_ENABLED", True)


class WordpressItem:
    def __init__(self, node, logger):
        self.node = node
        self.raw_body = self.node["content:encoded"]
        self.slug_changed = ""
        self.date_changed = ""
        self.image_errors = []
        # self.url_errors = []

        self.debug_content = {}
        self.logger = logger

    def prefilter_content(self, content):
        """
        FILTERS ARE CUMULATIVE
        cache the result of each filter which is run on the output from the previous filter
        """
        filter_config = getattr(
            settings, "WAGTAIL_WORDPRESS_IMPORT_PREFILTERS", DEFAULT_PREFILTERS
        )

        cached_result = content

        for filter in filter_config:
            function = import_string(filter["FUNCTION"])
            cached_result = function(cached_result, filter.get("OPTIONS"))
            if DEBUG_ENABLED:
                self.debug_content[function.__name__] = cached_result

        return cached_result

    def cleaned_title(self):
        return self.node["title"].strip()

    def cleaned_slug(self):
        """
        Oddly some page have no slug and some have illegal characters!
        If None make one from title.
        Also pass any slug through slugify to be sure and if it's chnaged make a note
        """

        if not self.node["wp:post_name"]:
            slug = slugify(self.cleaned_title())
            self.slug_changed = "blank slug"  # logging
        else:
            slug = slugify(self.node["wp:post_name"])

        # some slugs have illegal characters so it will be changed
        if slug != self.node["wp:post_name"]:
            self.slug_changed = "slug fixed"  # logging

        return slug

    def cleaned_first_published_at(self):
        return self.clean_date(self.node["wp:post_date_gmt"].strip())

    def cleaned_last_published_at(self):
        return self.clean_date(self.node["wp:post_modified_gmt"].strip())

    def cleaned_latest_revision_created_at(self):
        return self.clean_date(self.node["wp:post_modified_gmt"].strip())

    def clean_date(self, value):
        """
        We need a nice date to be able to save the page later. Some dates are not suitable
        date strings in the xml. If thats the case return a specific date so it can be saved
        and return the failure for logging
        """

        if value == "0000-00-00 00:00:00":
            # setting this date so it can be found in wagtail admin
            value = "1900-01-01 00:00:00"
            self.date_changed = True

        date_utc = "T".join(value.split(" "))
        date_formatted = make_aware(datetime.strptime(date_utc, "%Y-%m-%dT%H:%M:%S"))

        return date_formatted

    def cleaned_post_id(self):
        return int(self.node["wp:post_id"])

    def cleaned_post_type(self):
        return str(self.node["wp:post_type"].strip())

    def cleaned_link(self):
        return str(self.node["link"].strip())

    def body_stream_field(self, content):
        blocks_dict = BlockBuilder(content, self.node, self.logger).build()
        if DEBUG_ENABLED:
            self.debug_content["block_json"] = blocks_dict
        return json.dumps(blocks_dict)

    @cached_property
    def cleaned_data(self):
        return {
            "title": self.cleaned_title(),
            "slug": self.cleaned_slug(),
            "first_published_at": self.cleaned_first_published_at(),
            "last_published_at": self.cleaned_last_published_at(),
            "latest_revision_created_at": self.cleaned_latest_revision_created_at(),
            "body": self.body_stream_field(self.prefilter_content(self.raw_body)),
            "wp_post_id": self.cleaned_post_id(),
            "wp_post_type": self.cleaned_post_type(),
            "wp_link": self.cleaned_link(),
            "wp_block_json": self.debug_content.get("block_json"),
            "wp_processed_content": self.debug_content.get(
                "filter_transform_inline_styles_to_tags"
            ),
            "wp_normalized_styles": "",
            "wp_raw_content": self.debug_content.get("filter_linebreaks_wp"),
        }
