import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from wagtail.images.models import Image as ImportedImage

"""StreamField blocks"""


def build_block_quote_block(tag):
    block_dict = {
        "type": "block_quote",
        "value": {"quote": tag.text.strip(), "attribution": tag.cite},
    }
    return block_dict


def build_form_block(tag):
    block_dict = {"type": "raw_html", "value": str(tag)}
    return block_dict


def build_heading_block(tag):
    block_dict = {
        "type": "heading",
        "value": {"importance": tag.name, "text": tag.text},
    }
    return block_dict


def build_iframe_block(tag):
    block_dict = {
        "type": "raw_html",
        "value": '<div class="core-custom"><div class="responsive-iframe">{}</div></div>'.format(
            str(tag)
        ),
    }
    return block_dict


def build_image_block(tag):
    def get_image_id(src):
        return 1

    block_dict = {"type": "image", "value": get_image_id(tag.src)}
    return block_dict


def build_table_block(tag):
    block_dict = {"type": "raw_html", "value": str(tag)}
    return block_dict


def conf_html_tags_to_blocks():
    return getattr(
        settings,
        "WAGTAIL_WORDPRESS_IMPORTER_CONVERT_HTML_TAGS_TO_BLOCKS",
        [
            (
                "h1",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
                },
            ),
            (
                "h2",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
                },
            ),
            (
                "h3",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
                },
            ),
            (
                "h4",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
                },
            ),
            (
                "h5",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
                },
            ),
            (
                "h6",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
                },
            ),
            (
                "table",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_table_block",
                },
            ),
            (
                "iframe",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_iframe_block",
                },
            ),
            (
                "form",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_form_block",
                },
            ),
            (
                "img",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_image_block",
                },
            ),
            (
                "blockquote",
                {
                    "FUNCTION": "wagtail_wordpress_import.block_builder_defaults.build_block_quote_block",
                },
            ),
        ],
    )


"""Fall back StreamField block"""


def conf_fallback_block():
    return getattr(
        settings,
        "WAGTAIL_WORDPRESS_IMPORTER_FALLBACK_BLOCK",
        "wagtail_wordpress_import.block_builder_defaults.build_none_block_content",
    )


def build_none_block_content(cache, blocks):
    blocks.append({"type": "rich_text", "value": cache})
    cache = ""
    return cache


"""Rich Text Functions"""

# this is not what i'd expect to see but some images return text/html CDN maybe?
VALID_IMAGE_CONTENT_TYPES = [
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/webp",
    "text/html",
]

IMAGE_SRC_DOMAIN = "https://www.budgetsaresexy.com"  # note no trailing /


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

            if content_type and content_type.lower() not in VALID_IMAGE_CONTENT_TYPES:
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
