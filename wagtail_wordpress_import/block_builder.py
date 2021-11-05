from bs4 import BeautifulSoup
from django.conf import settings
from django.utils.module_loading import import_string

from wagtail_wordpress_import.block_builder_defaults import (
    conf_fallback_block,
    conf_html_tags_to_blocks,
)
from wagtail_wordpress_import.prefilters.handle_shortcodes import SHORTCODE_HANDLERS


def conf_promote_child_tags():
    return getattr(
        settings,
        "WAGTAIL_WORDPRESS_IMPORTER_PROMOTE_CHILD_TAGS",
        {
            "TAGS_TO_PROMOTE": ["iframe", "form", "blockquote"],
            "PARENTS_TO_REMOVE": ["p", "div", "span"],
        },
    )


class BlockBuilder:
    def __init__(self, value, node, logger):
        self.soup = BeautifulSoup(value, "lxml")
        self.blocks = []  # for each page this holds the sequence of StreamBlocks
        self.logged_items = {"processed": 0, "imported": 0, "skipped": 0, "items": []}
        self.node = node
        self.logger = logger

    def promote_child_tags(self):
        """
        Some HTML tags that can be at the top level, e.g. the parent is the
        body when using BS4 are getting placed inside or existed inside other HTML tags.
        We pull out these HTML tags and move them to the top level.
        returns: None
            but modifies the page soup
        """
        config_promote_child_tags = conf_promote_child_tags()
        promotee_tags = config_promote_child_tags["TAGS_TO_PROMOTE"]
        removee_tags = config_promote_child_tags["PARENTS_TO_REMOVE"]

        # for each registered shortcode handler add the element_name property
        # to the promotee_tags
        for handler in SHORTCODE_HANDLERS:
            if handler.is_top_level_html_tag:
                promotee_tags.append(handler().element_name)

        for promotee in promotee_tags:
            promotees = self.soup.findAll(promotee)
            for promotee in promotees:
                if promotee.parent.name in removee_tags:
                    promotee.parent.replace_with(promotee)

    def get_builder_function(self, element):
        """
        params
            element: an HTML tag
        returns:
            a function to parse the block from configuration
        """

        # registered shortcode custom tags
        conf_custom_tags = {}
        for handler in SHORTCODE_HANDLERS:
            cls = handler()
            conf_custom_tags[cls.element_name] = handler

        if element.name in conf_custom_tags:
            handler = conf_custom_tags[element.name]
            return "custom", handler

        # Detecting regular blocks to tags
        for tag, builder in conf_html_tags_to_blocks().items():
            if element.name == tag:
                return "html", import_string(builder)

    def build(self):
        """
        params:
            None
        returns:
            a list of block dicts

        The value to be processed here should have only top level HTML tags.
        The HTML is parsed to a sequence of StreamField blocks.
        If a HTML tag does have child blocks we should parse then inside the
        build_block_* method
        """
        soup = self.soup.find("body").findChildren(recursive=False)
        cached_fallback_value = (
            ""  # append fall back content here, by default it's a Rich Text block
        )
        cached_fallback_function = import_string(
            conf_fallback_block()
        )  # Rich Text block
        counter = 0
        for element in soup:  # each single top level tag
            counter += 1
            # the builder function for the element tag from config
            builder_function = self.get_builder_function(element)
            if builder_function:  # build a block
                if cached_fallback_value:
                    cached_fallback_value = cached_fallback_function(
                        cached_fallback_value,
                        self.blocks,
                    )  # before building a block write fall back cache to a block
                if builder_function[0] == "html":
                    self.blocks.append(builder_function[1](element))
                elif builder_function[0] == "custom":
                    self.blocks.append(builder_function[1]().construct_block(element))
            else:
                if element.text.strip():  # exclude a tag that is empty
                    cached_fallback_value += str(element)

            if cached_fallback_value and counter == len(
                soup
            ):  # the last tag so just build whats left in the fall back cache
                cached_fallback_value = cached_fallback_function(
                    cached_fallback_value, self.blocks
                )

        return self.blocks
