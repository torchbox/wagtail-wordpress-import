from django.conf import settings
import requests
import copy
from bs4 import BeautifulSoup, element
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from wagtail.images.models import Image as ImportedImage
from wagtail_wordpress_import.block_builder_defaults import (
    build_table_block,
    build_block_quote_block,
    build_form_block,
    build_heading_block,
    build_iframe_block,
    build_image_block,
)

TAGS_TO_BLOCKS = [
    "table",
    "iframe",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "img",
    "blockquote",
]


def conf_promote_child_tags():
    return getattr(
        settings,
        "WAGTAIL_WORDPRESS_IMPORTER_PROMOTE_CHILD_TAGS",
        {
            "TAGS_TO_PROMOTE": ["iframe", "form", "blockquote"],
            "PARENTS_TO_REMOVE": ["p", "div", "span"],
        },
    )


# this is not what i'd expect to see but some images return text/html CDN maybe?
VALID_IMAGE_CONTENT_TYPES = [
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/webp",
    "text/html",
]

IMAGE_SRC_DOMAIN = "https://www.budgetsaresexy.com"  # note no trailing /


class BlockBuilder:
    def __init__(self, value, node, logger):
        self.soup = BeautifulSoup(value, "lxml")
        self.blocks = []
        self.logged_items = {"processed": 0, "imported": 0, "skipped": 0, "items": []}
        self.node = node
        self.logger = logger

    def promote_child_tags(self):
        """
        pull out these HTML tags and make sure they are placed at the top
        level as they don't need to be in enclosing tags for our purposes.
        """
        config_promote_child_tags = conf_promote_child_tags()
        promotee_tags = config_promote_child_tags["TAGS_TO_PROMOTE"]
        removee_tags = config_promote_child_tags["PARENTS_TO_REMOVE"]

        for promotee in promotee_tags:
            promotees = self.soup.findAll(promotee)
            for promotee in promotees:
                if promotee.parent.name in removee_tags:
                    promotee.parent.replace_with(promotee)

    def build(self):
        soup = self.soup.find("body").findChildren(recursive=False)
        block_value = str("")
        counter = 0
        for tag in soup:
            counter += 1
            """
            the process here loops though each soup tag to discover
            the block type to use
            """

            # RICHTEXT
            if tag.name not in TAGS_TO_BLOCKS:
                block_value += str(self.image_linker(str(tag)))

            if tag.name == "table":
                if len(block_value) > 0:
                    self.blocks.append({"type": "rich_text", "value": block_value})
                    block_value = str("")
                self.blocks.append(build_table_block(tag))

            if tag.name == "iframe":
                if len(block_value) > 0:
                    self.blocks.append({"type": "rich_text", "value": block_value})
                    block_value = str("")
                self.blocks.append(build_iframe_block(tag))

            if tag.name == "form":
                if len(block_value) > 0:
                    self.blocks.append({"type": "rich_text", "value": block_value})
                    block_value = str("")
                self.blocks.append(build_form_block(tag))

            if (
                tag.name == "h1"
                or tag.name == "h2"
                or tag.name == "h3"
                or tag.name == "h4"
                or tag.name == "h5"
                or tag.name == "h6"
            ):
                if len(block_value) > 0:
                    self.blocks.append({"type": "rich_text", "value": block_value})
                    block_value = str("")
                options = {}
                options["importance"] = tag.name
                self.blocks.append(build_heading_block(tag))

            if tag.name == "img":
                if len(block_value) > 0:
                    self.blocks.append({"type": "rich_text", "value": block_value})
                    block_value = str("")
                self.blocks.append(build_image_block(tag))

            if tag.name == "blockquote":
                if len(block_value) > 0:
                    self.blocks.append({"type": "rich_text", "value": block_value})
                    block_value = str("")
                options = {}
                options["cite"] = ""
                if tag.attrs and tag.attrs.get("cite"):
                    options["cite"] = tag.attrs["cite"]
                self.blocks.append(build_block_quote_block(tag))

            if counter == len(soup) and len(block_value) > 0:
                # when we reach the end and something is in the
                # block_value just output and clear
                self.blocks.append({"type": "rich_text", "value": block_value})
                block_value = str("")

        return self.blocks

    def image_linker(self, tag):
        soup = BeautifulSoup(tag, "html.parser", exclude_encodings=True)
        images = soup.find_all("img")

        for image in images:
            image_saved = self.get_image(image)
            if image_saved:
                alignment = self.get_alignment_class(image)
                img_alt = image.attrs["alt"] if "alt" in image.attrs else None
                tag = '<embed embedtype="image" id="{}" alt="{}" format="{}" />'.format(
                    image_saved.id, img_alt, alignment
                )

        return tag

    def get_alignment_class(self, image):
        alignment = "fullwidth"

        if "class" in image.attrs:
            if "align-left" in image.attrs["class"]:
                alignment = "left"
            elif "align-right" in image.attrs["class"]:
                alignment = "right"

        return alignment

    def get_image(self, image):

        if image.get("src"):
            name = image.get("src").split("/")[-1]  # need the last part
            temp = NamedTemporaryFile(delete=True)
            image_src = check_image_src(image.get("src")).strip("/")
        else:
            self.logged_items["items"].append(
                {
                    "id": self.node.get("wp:post_id"),
                    "title": self.node.get("title"),
                    "link": self.node.get("link"),
                    "reason": "no src provided",
                }
            )
            self.logger.images.append(
                {
                    "id": self.node.get("wp:post_id"),
                    "title": self.node.get("title"),
                    "link": self.node.get("link"),
                    "reason": "no src provided",
                }
            )
            return

        try:
            image_exists = ImportedImage.objects.get(title=name)
            return image_exists

        except ImportedImage.DoesNotExist:

            try:
                response = requests.get(image_src, timeout=10)
                status_code = response.status_code
                content_type = response.headers.get("Content-Type")

                if (
                    content_type
                    and content_type.lower() not in VALID_IMAGE_CONTENT_TYPES
                ):
                    self.logged_items["items"].append(
                        {
                            "id": self.node.get("wp:post_id"),
                            "title": self.node.get("title"),
                            "link": self.node.get("link"),
                            "reason": "invalid image types match or no content type",
                        }
                    )
                    self.logger.images.append(
                        {
                            "id": self.node.get("wp:post_id"),
                            "title": self.node.get("title"),
                            "link": self.node.get("link"),
                            "reason": "invalid image types match or no content type",
                        }
                    )
                    return

                if status_code == 200:
                    temp.name = name
                    temp.write(response.content)
                    temp.flush()
                    new_image = ImportedImage(file=File(file=temp), title=name)
                    new_image.save()
                    return new_image

            except requests.exceptions.ConnectionError:
                self.logged_items["items"].append(
                    {
                        "id": self.node.get("wp:post_id"),
                        "title": self.node.get("title"),
                        "link": self.node.get("link"),
                        "reason": "connection error",
                    }
                )
                self.logger.images.append(
                    {
                        "id": self.node.get("wp:post_id"),
                        "title": self.node.get("title"),
                        "link": self.node.get("link"),
                        "reason": "connection error",
                    }
                )


def check_image_src(src):
    # some images have relative src values
    if not src.startswith("http"):
        print(
            "WARNING: relative file {}. Image may be broken, trying with domain name prepended. ".format(
                src
            )
        )
        return IMAGE_SRC_DOMAIN + "/" + src
    return src
