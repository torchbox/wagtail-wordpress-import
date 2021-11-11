import json
from datetime import datetime
from functools import cached_property
from xml.dom import pulldom
from django.utils.module_loading import import_string

from bs4 import BeautifulSoup
from django.apps import apps
from django.utils.module_loading import import_string
from django.utils.text import slugify
from django.utils.timezone import make_aware
from wagtail.core.models import Page
from wagtail_wordpress_import.block_builder import BlockBuilder
from wagtail_wordpress_import.functions import node_to_dict
from wagtail_wordpress_import.importers.wordpress_defaults import (
    category_name_min_length,
    debug_enabled,
    default_prefilters,
    get_category_model,
    yoast_plugin_config,
    yoast_plugin_enabled,
    category_plugin_enabled,
)
from wagtail_wordpress_import.prefilters.linebreaks_wp_filter import (
    filter_linebreaks_wp,
)


class WordpressImporter:
    def __init__(self, xml_file_path):
        self.xml_file = xml_file_path
        self.imported_pages = []
        self.page_link_errors = []

    def run(self, *args, **kwargs):
        self.logger = kwargs["logger"]
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
            """
            Each node represents a tag in the xml.
            `event` is true for a start element.
            """
            if event == pulldom.START_ELEMENT and node.tagName == "item":
                xml_doc.expandNode(node)
                item = node_to_dict(node)
                self.logger.processed += 1

                if (
                    item.get("wp:post_type") in kwargs["page_types"]
                    and item.get("wp:status") in kwargs["page_statuses"]
                ):

                    wordpress_item = WordpressItem(item, self.logger)

                    try:
                        page = self.page_model_instance.objects.get(
                            wp_post_id=wordpress_item.cleaned_data.get("wp_post_id")
                        )
                    except self.page_model_instance.DoesNotExist:
                        page = self.page_model_instance()

                    # add categories for this page if categories plugin is enabled
                    if category_plugin_enabled() and get_category_model():
                        self.connect_page_categories(
                            page, import_string(get_category_model()), item
                        )

                    page.import_wordpress_data(wordpress_item.cleaned_data)

                    if item.get("wp:status") == "draft":
                        setattr(page, "live", False)
                    else:
                        setattr(page, "live", True)

                    if page.id:
                        page.save()
                        self.logger.imported += 1
                        self.logger.items.append(
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
                        self.logger.imported += 1
                        self.logger.items.append(
                            {
                                "id": page.id,
                                "title": page.title,
                                "link": item.get("link"),
                                "result": "created",
                                "reason": "existed",
                                "datecheck": wordpress_item.date_changed,
                                "slugcheck": wordpress_item.slug_changed,
                            }
                        )

                    self.imported_pages.append(page)

                else:
                    self.logger.skipped += 1
                    self.logger.items.append(
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
                self.logger.items.append(
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
            self.logger.log_progress()

        self.connect_richtext_page_links(self.imported_pages)

    def analyze_html(self, html_analyzer, *, page_types, page_statuses):
        xml_doc = pulldom.parse(self.xml_file)

        for event, node in xml_doc:
            """
            Each node represents a tag in the xml.
            `event` is true for a start element.
            """
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

    def connect_richtext_page_links(self, imported_pages):
        """
        Update the StreamField content of each page by reconstructing
        the existing blocks. Only update rich_text blocks by analysing the anchor links
        in update_rich_text_page_links()
        """
        for page in imported_pages:
            stream_data = page.body._raw_data
            reconstructed_blocks = []
            for block in stream_data:
                del block["id"]  # these get created on save so lose the old id
                if block["type"] == "rich_text":
                    block["value"] = str(self.update_rich_text_page_links(block, page))
                reconstructed_blocks.append(block)
            page.body = json.dumps(stream_data)
            page.save()

    def update_rich_text_page_links(self, block, page):
        """
        Get all the anchor tags (bs4) and replace the anchor tag with
        <a id="{wagtail page id}" linktype="page">{the current anchor text}</a>
        If a wagtail page cannot be found for the anchor link, ignore it but
        save to the log.
        """
        soup = BeautifulSoup(block["value"], "html.parser")
        links = soup.findAll("a")

        for link in links:
            page_link = self.get_page(link.attrs.get("href"), page)
            if page_link:
                new_tag = soup.new_tag("a")
                new_tag.attrs["id"] = page_link.id
                new_tag.attrs["linktype"] = "page"
                new_tag.string = link.text
                link.replace_with(new_tag)
        return soup

    def get_page(self, link, page):
        try:
            if debug_enabled():
                self.logger.page_link_errors.append((link, page))
            return self.page_model_instance.objects.get(wp_link=link)
        except self.page_model_instance.DoesNotExist:
            pass

    def connect_page_categories(self, page, category_model, item):
        if "category" in item.keys():
            categories = [
                category
                for category in item["category"]
                if category and len(category) > category_name_min_length()
            ]

            page_categories = []

            for name in categories:
                category, created = category_model.objects.get_or_create(name=name)
                page_categories.append(category)

            page.categories = page_categories


class WordpressItem:
    def __init__(self, node, logger):
        self.node = node
        self.raw_body = self.node["content:encoded"]
        self.slug_changed = ""
        self.date_changed = ""
        self.image_errors = []

        self.debug_content = {}
        self.logger = logger

    def prefilter_content(self, content):
        """
        FILTERS ARE CUMULATIVE: Each filter receives the output from the previous filter.
        """
        cached_result = content

        for filter in default_prefilters():
            function = import_string(filter["FUNCTION"])
            cached_result = function(cached_result, filter.get("OPTIONS"))
            if debug_enabled():
                self.debug_content[function.__name__] = cached_result

        return cached_result

    def cleaned_title(self):
        return self.node["title"].strip()

    def cleaned_slug(self):
        """
        Clean up the slugs from the XML import file
        Some pages have no slug and some have unexpected characters.
        If a slug is not provided create one from page title.
        If a slug is changed it's recorded in the logger
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
        We need a proper date format.
        Some dates are not suitable date strings in the xml, if so return a
        specific date so it can be saved in Wagtail and record it in the logger.
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
        builder = BlockBuilder(content, self.node, self.logger)
        builder.promote_child_tags()
        blocks_dict = builder.build()
        if debug_enabled():
            self.debug_content["block_json"] = blocks_dict
        return json.dumps(blocks_dict)

    def get_yoast_description_value(self):
        """
        The Wordpress yoast plugin seems to have different fields available on
        a item record and not always contains the _yoast_wpseo_metadesc field.

        This parses the wp:postmeta field to check if a _yoast_wpseo_metadesc
        is available. If not it returns a blank string or the default description field
        from the XML import file <item><description>...</description></item>
        """
        meta_value = ""

        if yoast_plugin_config()["xml_item_key"] in self.node.keys():
            for item in self.node.get(yoast_plugin_config()["xml_item_key"]):

                if isinstance(item, dict):
                    meta_key_values = list(item.values())

                    if (
                        meta_key_values[0]
                        == yoast_plugin_config()["description_key_value"]
                    ):
                        meta_value = meta_key_values[1] or ""

        if not meta_value:
            meta_value = self.node.get("description") or ""

        return meta_value

    def cleaned_search_description(self):
        if yoast_plugin_enabled():
            return self.get_yoast_description_value().strip()

        if self.node.get("description") is not None:
            return self.node.get("description").strip()
        else:
            return ""

    @cached_property
    def cleaned_data(self):
        """
        I'm leaving a note here because later on we will be adding the ability
        for a developer to specify fields we haven't included in the import
        process. That'll need to happend starting here. Check out self.cleaned_search_description()
        which imports to a standard Wagtail field.

        This came out of dealing with the Yoast search_description field which we have
        included and can be configured to accept different values that are in wp:postmeta keys
        """

        return {
            "title": self.cleaned_title(),
            "slug": self.cleaned_slug(),
            "first_published_at": self.cleaned_first_published_at(),
            "last_published_at": self.cleaned_last_published_at(),
            "latest_revision_created_at": self.cleaned_latest_revision_created_at(),
            "body": self.body_stream_field(self.prefilter_content(self.raw_body)),
            "search_description": self.cleaned_search_description(),
            "wp_post_id": self.cleaned_post_id(),
            "wp_post_type": self.cleaned_post_type(),
            "wp_link": self.cleaned_link(),
            "wp_block_json": self.debug_content.get("block_json"),
            "wp_processed_content": self.debug_content.get(
                "filter_transform_inline_styles"
            ),
            "wp_normalized_styles": "",
            "wp_raw_content": self.debug_content.get("filter_linebreaks_wp"),
        }
