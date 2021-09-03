from django.core.management.base import BaseCommand
from wagtail_xmlimport.functions import *


class Command(BaseCommand):
    help = """Utils to output xml structure to a file."""

    def add_arguments(self, parser):
        parser.add_argument("xmlfile", type=str)
        parser.add_argument("--tags", type=str)
        parser.add_argument("--limit", type=int, default=3)

    def handle(self, *args, **options):
        self.xmlname = options["xmlfile"].split(".")[0]
        if options["tags"] == "channel" and options["xmlfile"] == "all.xml":
            # this does rely on the filename for the complete xml dataset be all.xml
            self.stdout.write(
                self.style.ERROR(
                    "channel output does not work with the all.xml dataset"
                )
            )
            exit()
        if options["tags"] == "items":
            self.parse_items(options["xmlfile"], options["limit"])
        if options["tags"] == "channel":
            self.parse_channel(options["xmlfile"])
        if options["tags"] == "wp:categories":
            self.parse_categories(options["xmlfile"], options["limit"])
        if options["tags"] == "wp:tag":
            self.parse_tags(options["xmlfile"], options["limit"])
        if options["tags"] == "items-attachments":
            self.parse_attachments(options["xmlfile"], options["limit"])
        if not options["tags"]:
            self.stdout.write(self.style.ERROR("did you forget the --tags option?"))

    def parse_channel(self, xmlfile):
        # don't need a counter here as there's only one channel anyway
        self.empty_log(f"log/{self.xmlname}_channel.txt")
        doc = pulldom.parse("xml/" + xmlfile)
        for event, node in doc:
            if event == pulldom.START_ELEMENT and node.tagName == "channel":
                doc.expandNode(node)
                dict = node_to_dict(node)
                self.write_divider(f"log/{self.xmlname}_channel.txt")
                for key in dict:
                    self.write_tag(f"log/{self.xmlname}_channel.txt", key)

    def parse_items(self, xmlfile, limit):
        self.empty_log(f"log/{self.xmlname}_items.txt")
        counter = limit  # use this to count down to get a smallish sample
        doc = pulldom.parse("xml/" + xmlfile)
        for event, node in doc:
            if event == pulldom.START_ELEMENT and node.tagName == "item":
                doc.expandNode(node)
                dict = node_to_dict(node)
                self.write_divider(f"log/{self.xmlname}_items.txt")
                for key in dict:
                    self.write_tag(f"log/{self.xmlname}_items.txt", key)
                counter -= 1
                if counter == 0:
                    break

    def parse_categories(self, xmlfile, limit):
        self.empty_log(f"log/{self.xmlname}_categories.txt")
        counter = limit  # use this to count down to get a smallish sample
        doc = pulldom.parse("xml/" + xmlfile)
        for event, node in doc:
            if event == pulldom.START_ELEMENT and node.tagName == "wp:category":
                doc.expandNode(node)
                dict = node_to_dict(node)
                self.write_divider(f"log/{self.xmlname}_categories.txt")
                for key in dict:
                    self.write_tag(f"log/{self.xmlname}_categories.txt", key)
                counter -= 1
                if counter == 0:
                    break

    def parse_tags(self, xmlfile, limit):
        self.empty_log(f"log/{self.xmlname}_tags.txt")
        counter = limit  # use this to count down to get a smallish sample
        doc = pulldom.parse("xml/" + xmlfile)
        for event, node in doc:
            if event == pulldom.START_ELEMENT and node.tagName == "wp:tag":
                doc.expandNode(node)
                dict = node_to_dict(node)
                self.write_divider(f"log/{self.xmlname}_tags.txt")
                for key in dict:
                    self.write_tag(f"log/{self.xmlname}_tags.txt", key)
                counter -= 1
                if counter == 0:
                    break

    def parse_attachments(self, xmlfile, limit):  # media/assets
        self.empty_log(f"log/{self.xmlname}_attachments.txt")
        counter = limit  # use this to count down to get a smallish sample
        doc = pulldom.parse("xml/" + xmlfile)
        for event, node in doc:
            if event == pulldom.START_ELEMENT and node.tagName == "item":
                doc.expandNode(node)
                dict = node_to_dict(node)
                self.write_divider(f"log/{self.xmlname}_attachments.txt")
                # check for wp:post_type == attachment
                if dict["wp:post_type"] == "attachment":
                    for key in dict:
                        if key == "wp:post_type":
                            self.write_tag(f"log/{self.xmlname}_attachments.txt", key, "<![CDATA[attachment]]>")
                        if key == "guid":
                            self.write_tag(f"log/{self.xmlname}_attachments.txt", key, dict[key])
                        self.write_tag(f"log/{self.xmlname}_attachments.txt", key, "")
                    counter -= 1
                    if counter == 0:
                        break

    def empty_log(self, file_name):
        open(file_name, "w").close()

    def write_divider(self, file_name):
        dashes = "-" * 20 + "\n"
        with open(file_name, "a") as tagsfile:
            tagsfile.write(dashes)

    def write_tag(self, file_name, tag, extra=""):
        with open(file_name, "a") as tagsfile:
            tagsfile.write((f"{tag} {extra}\n"))
