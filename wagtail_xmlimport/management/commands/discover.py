from django.core.management.base import BaseCommand
from wagtail_xmlimport.functions import *


class Command(BaseCommand):
    help = """Utils to output xml structure to a file. 
    Items is store in log/itemtags.txt. Channels is stored in log/channeltags.txt"""

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
            open(f"log/{self.xmlname}_items.txt", "w").close()  # empty the file first
            self.parse_items(options["xmlfile"], options["limit"])
        if options["tags"] == "channel":
            open(f"log/{self.xmlname}_channel.txt", "w").close()  # empty the file first
            self.parse_channel(options["xmlfile"])
        if not options["tags"]:
            self.stdout.write(self.style.ERROR("did you forget the --tags option?"))

    def parse_channel(self, xmlfile):
        # don't need a counter here as there's only one channel anyway
        doc = pulldom.parse("xml/" + xmlfile)
        for event, node in doc:
            if event == pulldom.START_ELEMENT and node.tagName == "channel":
                doc.expandNode(node)
                dict = node_to_dict(node)
                with open(f"log/{self.xmlname}_channel.txt", "a") as tagsfile:
                    tagsfile.write("----------\n")
                for key in dict:
                    with open(f"log/{self.xmlname}_channel.txt", "a") as tagsfile:
                        tagsfile.write((f"{key}\n"))

    def parse_items(self, xmlfile, limit):
        counter = limit  # use this to count down to get a smallish sample
        doc = pulldom.parse("xml/" + xmlfile)
        for event, node in doc:
            if event == pulldom.START_ELEMENT and node.tagName == "item":
                doc.expandNode(node)
                dict = node_to_dict(node)
                with open(f"log/{self.xmlname}_items.txt", "a") as tagsfile:
                    tagsfile.write("----------\n")
                for key in dict:
                    with open(f"log/{self.xmlname}_items.txt", "a") as tagsfile:
                        tagsfile.write((f"{key}\n"))
                counter -= 1
                if counter == 0:
                    break
