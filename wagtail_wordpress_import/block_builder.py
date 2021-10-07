import requests
from bs4 import BeautifulSoup
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from wagtail.images.models import Image as ImportedImage

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

IRELLEVANT_PARENTS = ["p", "div", "span"]

VALID_IMAGE_CONTENT_TYPES = [
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/webp",
    "text/html",  # this is not what i'd expect to see but some images retun this CDN maybe?
]

IMAGE_SRC_DOMAIN = "https://www.budgetsaresexy.com"  # note no trailing /


class BlockBuilder:
    def __init__(self, value, node):
        self.soup = BeautifulSoup(value, "lxml", exclude_encodings=True)
        self.blocks = []
        self.logged_items = {"processed": 0, "imported": 0, "skipped": 0, "items": []}
        self.node = node
        self.set_up()

    def set_up(self):
        """
        iframes, forms can get put inside a p tag, pull them out
        extend this to add further tags
        """
        for iframe in self.soup.find_all("iframe"):
            parent = iframe.previous_element
            if parent.name in IRELLEVANT_PARENTS:
                parent.replaceWith(iframe)

        for form in self.soup.find_all("form"):
            parent = form.previous_element
            if parent.name in IRELLEVANT_PARENTS:
                parent.replaceWith(form)

        for blockquote in self.soup.find_all("blockquote"):
            parent = blockquote.previous_element
            if parent.name in IRELLEVANT_PARENTS:
                parent.replaceWith(blockquote)

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

            # TABLE
            if tag.name == "table":
                if len(block_value) > 0:
                    self.blocks.append({"type": "rich_text", "value": block_value})
                    block_value = str("")
                self.blocks.append({"type": "raw_html", "value": str(tag)})

            # IFRAME/EMBED
            if tag.name == "iframe":
                if len(block_value) > 0:
                    self.blocks.append({"type": "rich_text", "value": block_value})
                    block_value = str("")
                self.blocks.append(
                    {
                        "type": "raw_html",
                        "value": '<div class="core-custom"><div class="responsive-iframe">{}</div></div>'.format(
                            str(tag)
                        ),
                    }
                )

            # FORM
            if tag.name == "form":
                if len(block_value) > 0:
                    self.blocks.append({"type": "rich_text", "value": block_value})
                    block_value = str("")
                self.blocks.append({"type": "raw_html", "value": str(tag)})

            # HEADING
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
                self.blocks.append(
                    {
                        "type": "heading",
                        "value": {"importance": tag.name, "text": str(tag.text)},
                    }
                )

            # IMAGE
            if tag.name == "img":
                if len(block_value) > 0:
                    self.blocks.append({"type": "rich_text", "value": block_value})
                    block_value = str("")
                self.blocks.append({"type": "raw_html", "value": str(tag)})

            # BLOCKQUOTE
            if tag.name == "blockquote":
                if len(block_value) > 0:
                    self.blocks.append({"type": "rich_text", "value": block_value})
                    block_value = str("")
                cite = ""
                if tag.attrs and tag.attrs.get("cite"):
                    cite = str(tag.attrs["cite"])
                self.blocks.append(
                    {
                        "type": "block_quote",
                        "value": {"quote": str(tag.text), "attribution": cite},
                    }
                )

            if counter == len(soup) and len(block_value) > 0:
                # when we reach the end and something is in the
                # block_value just output and clear
                self.blocks.append({"type": "rich_text", "value": block_value})
                block_value = str("")

        # print(self.logged_items)
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
            self.logged_items["items"].append({
                "id": self.node.get("id"),
                "title": self.node.get("title"),
                "link": self.node.get("link"),
                "reason": "no src provided",
            })                
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
                    self.logged_items["items"].append({
                        "id": self.node.get("id"),
                        "title": self.node.get("title"),
                        "link": self.node.get("link"),
                        "reason": "invalid image types match or no content type",
                    }) 
                    return

                if status_code == 200:
                    temp.name = name
                    temp.write(response.content)
                    temp.flush()
                    new_image = ImportedImage(file=File(file=temp), title=name)
                    new_image.save()
                    return new_image

            except requests.exceptions.ConnectionError:
                self.logged_items["items"].append({
                    "id": self.node.get("id"),
                    "title": self.node.get("title"),
                    "link": self.node.get("link"),
                    "reason": "connection error",
                })


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
