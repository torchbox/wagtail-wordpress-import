import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.utils.module_loading import import_string
from wagtail.documents import get_document_model
from wagtail.images import get_image_model

ImportedImage = get_image_model()
ImportedDocument = get_document_model()


def conf_html_tags_to_blocks():
    return getattr(
        settings,
        "WAGTAIL_WORDPRESS_IMPORTER_CONVERT_HTML_TAGS_TO_BLOCKS",
        {
            "h1": "wagtail_wordpress_import.block_builder_defaults.build_heading_block",
            "table": "wagtail_wordpress_import.block_builder_defaults.build_table_block",
            "iframe": "wagtail_wordpress_import.block_builder_defaults.build_iframe_block",
            "form": "wagtail_wordpress_import.block_builder_defaults.build_form_block",
            "img": "wagtail_wordpress_import.block_builder_defaults.build_image_block",
            "blockquote": "wagtail_wordpress_import.block_builder_defaults.build_block_quote_block",
        },
    )


def fetch_url(src, allow_redirects=True):
    """general purpose url fetcher with ability to pass in own config"""
    try:
        response = requests.get(
            src,
            **getattr(
                settings,
                "WAGTAIL_WORDPRESS_IMPORTER_REQUESTS_SETTINGS",
                {
                    "headers": {"User-Agent": "WagtailWordpressImporter"},
                    "timeout": 5,
                    "stream": True,
                    "allow_redirects": allow_redirects,
                },
            ),
        )
        status = True if response.status_code == 200 else False
        return response, status, response.headers.get("content-type")
    except requests.ConnectionError:
        print(f"ConnectionError: {src}")
        return None, False, None
    except requests.HTTPError:
        print(f"HTTPError: {src}")
        return None, False, None
    except requests.RequestException:
        print(f"RequestException: {src}")
        return None, False, None
    except requests.ReadTimeout:
        print(f"ReadTimeout: {src}")
        return None, False, None
    except requests.Timeout:
        print(f"Timeout: {src}")
        return None, False, None
    except requests.ConnectTimeout:
        print(f"ConnectTimeout: {src}")
        return None, False, None


# FUNCTIONS FOR IMAGES


def image_linker(html):
    """
    params
    ======
        html: html from a single rich_text block

    returns
    =======
        string: the html with img tags modified

    BS4 performs a find and replace on all img tags found in the HTML.
    If the image can be retrieved from the remote site and saved into a Wagtail ImageModel
    the soup is modified.
    """
    soup = BeautifulSoup(html, "html.parser")
    images = soup.find_all("img")
    for image in images:
        if image.attrs and image.attrs.get("src"):
            image_src = get_absolute_src(
                image.attrs["src"],
                getattr(settings, "WAGTAIL_WORDPRESS_IMPORTER_SOURCE_DOMAIN"),
            )
            saved_image = get_or_save_image(image_src)
            if saved_image:
                image_embed = soup.new_tag("embed")
                image_embed.attrs["embedtype"] = "image"
                image_embed.attrs["id"] = saved_image.id
                image_embed.attrs["alt"] = get_image_alt(image)
                image_embed.attrs["format"] = get_alignment_class(image)
                image.replace_with(image_embed)
        else:
            print(f"IMAGE HAS NO SRC: {image}")

    return str(soup)


def get_or_save_image(src):
    image_file_name = get_image_file_name(src)
    existing_image = image_exists(image_file_name)
    if not existing_image:
        response, valid, type = fetch_url(src)
        if valid and (
            type
            in getattr(
                settings,
                "WAGTAIL_WORDPRESS_IMPORTER_VALID_IMAGE_CONTENT_TYPES",
                [
                    "image/gif",
                    "image/jpeg",
                    "image/png",
                    "image/webp",
                ],
            )
        ):
            temp_image = NamedTemporaryFile(delete=True)
            temp_image.name = image_file_name
            temp_image.write(response.content)
            temp_image.flush()
            retrieved_image = ImportedImage(
                file=File(file=temp_image), title=image_file_name
            )
            retrieved_image.save()
            temp_image.close()
            return retrieved_image
        else:
            print(f"RECEIVED INVALID IMAGE RESPONSE: {src}")
    return existing_image


# FUNCTIONS FOR DOCUMENTS


def document_linker(html):
    """
    params
    ======
        html: html from a single rich_text block

    returns
    =======
        string: the html with anchor links modified

    BS4 performs a find and replace on all img tags found in the HTML.
    If the image can be retrived from the remote site and saved into a Wagtail ImageModel
    the soup is modified.
    """
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.find_all("a")
    for anchor in anchors:
        if anchor.attrs and anchor.attrs.get("href"):
            anchor_href = get_absolute_src(
                anchor.attrs["href"],
                getattr(settings, "WAGTAIL_WORDPRESS_IMPORTER_SOURCE_DOMAIN"),
            )
            anchor_inner_content = anchor.text
            saved_document = get_or_save_document(anchor_href)
            if saved_document:
                document_embed = soup.new_tag("a")
                document_embed.attrs["linktype"] = "document"
                document_embed.attrs["id"] = saved_document.id
                document_embed.string = anchor_inner_content
                anchor.replace_with(document_embed)
        else:
            print(f"DOCUMENT HAS NO HREF: {anchor}")

    return str(soup)


def get_or_save_document(href):
    file_type = href.split(".")[-1]
    if file_type in getattr(
        settings,
        "",
        [
            "pdf",
            "ppt",
            "docx",
        ],
    ):
        document_file_name = get_document_file_name(href)
        existing_document = document_exists(document_file_name)
        if not existing_document:
            response, valid, type = fetch_url(href)
            if valid and (
                type
                in getattr(
                    settings,
                    "",
                    [
                        "application/pdf",
                        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    ],
                )
            ):
                temp_document = NamedTemporaryFile(delete=True)
                temp_document.name = document_file_name
                temp_document.write(response.content)
                temp_document.flush()
                retrieved_document = ImportedDocument(
                    file=File(file=temp_document), title=document_file_name
                )
                retrieved_document.save()
                temp_document.close()
                return retrieved_document
            else:
                print(f"RECEIVED INVALID DOCUMENT RESPONSE: {href}")
        return existing_document


# STREAMFIELD BLOCKS


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


# FALLBACK STREAMFIELD BLOCKS


def conf_fallback_block():
    return getattr(
        settings,
        "WAGTAIL_WORDPRESS_IMPORTER_FALLBACK_BLOCK",
        "wagtail_wordpress_import.block_builder_defaults.build_richtext_block_content",
    )


def build_richtext_block_content(html, blocks):
    """
    image_linker is called to link up and retrive the remote image
    document_linker is called to link up and retrive the remote documents
    filters are called to replace inline shortcodes
    """
    html = image_linker(html)
    html = document_linker(html)
    for inline_shortcode_handler in getattr(
        settings, "WAGTAIL_WORDPRESS_IMPORTER_INLINE_SHORTCODE_HANDLERS", []
    ):
        function = import_string(inline_shortcode_handler).construct_html_tag
        html = function(html)
    blocks.append({"type": "rich_text", "value": html})
    html = ""
    return html


# RICH TEXT FUNCTIONS


def get_image_alt(img_tag):
    return img_tag.attrs["alt"] if "alt" in img_tag.attrs else None


def get_image_file_name(src):
    return src.split("/")[-1] if src else None  # need the last part


def get_document_file_name(src):
    return src.split("/")[-1] if src else None  # need the last part


def image_exists(name):
    try:
        return ImportedImage.objects.get(title=name)
    except ImportedImage.DoesNotExist:
        pass


def document_exists(name):
    try:
        return ImportedDocument.objects.get(title=name)
    except ImportedDocument.DoesNotExist:
        pass


# GENERAL FUNCTIONS


def get_absolute_src(src, domain_prefix=None):
    src = src.lstrip("/")
    if not src.startswith("http") and domain_prefix:
        return domain_prefix + "/" + src
    return src


def get_alignment_class(image):
    alignment = "fullwidth"

    if "class" in image.attrs:
        if "align-left" in image.attrs["class"]:
            alignment = "left"
        elif "align-right" in image.attrs["class"]:
            alignment = "right"

    return alignment
