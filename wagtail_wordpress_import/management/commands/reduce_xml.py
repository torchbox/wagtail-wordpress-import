import json
import os
import xml.etree.ElementTree as ET

from django.core.management.base import BaseCommand


# register all namespaces to keep them when the modified xml is saved
def register_all_namespaces(filename):
    namespaces = dict([node for _, node in ET.iterparse(filename, events=["start-ns"])])
    for ns in namespaces:
        ET.register_namespace(ns, namespaces[ns])


def generate_stats_file(file_path, type_stats):
    stats_filename = f"stats-{file_path.split('/')[-1]}.json"
    f = open(stats_filename, "w")
    f.write(json.dumps(type_stats, indent=2))
    return stats_filename


class Command(BaseCommand):

    help = """Utils to reduce xml file size by removing unwanted tags."""

    """
    Tags to be removed item > wp:comment
    """

    def add_arguments(self, parser):
        parser.add_argument("xml_file", type=str, help="The full path to your xml file")

    def get_xml_file(self, xml_file):

        if os.path.exists(xml_file):
            return xml_file

        self.stdout.write(
            self.style.ERROR(f"The xml file `{xml_file}` cannot be found")
        )
        exit()

    def handle(self, *args, **options):
        file_path = self.get_xml_file(options["xml_file"])
        self.stdout.write(self.style.WARNING("Reducing ..."))
        self.stdout.write(
            self.style.NOTICE(
                "If this is a large file and has many depths it will take some time to complete"
            )
        )
        register_all_namespaces(file_path)

        num_lines_original = sum(1 for line in open(file_path))
        num_lines_original_formatted = "{:,}".format(num_lines_original)

        self.stdout.write(f"Original #lines {num_lines_original_formatted}")

        ofile = file_path.split(".")[0]
        output_file_name = f"{ofile}-reduced.xml"
        output_file_path = f"{output_file_name}"

        tree = ET.parse(file_path)
        wp = "{http://wordpress.org/export/1.2/}"
        items = tree.getroot()[0].findall("item")
        item_types = []
        item_statuses = []
        for item in items:
            comments = item.findall(f"{wp}comment")
            item_type = item.find(f"{wp}post_type").text
            item_status = item.find(f"{wp}status").text
            if item_type not in item_types:
                item_types.append(item_type)
            if item_status not in item_statuses:
                item_statuses.append(item_status)
            for comment in comments:
                item.remove(comment)

        tree.write(output_file_path)

        type_stats = [
            {
                type: len(
                    tree.getroot()[0].findall(f".//item/[{wp}post_type='{type}']")
                ),
                "status_counts": {
                    status: len(
                        tree.getroot()[0].findall(
                            f".//item/[{wp}post_type='{type}'][{wp}status='{status}']"
                        )
                    )
                    for status in item_statuses
                },
            }
            for type in item_types
        ]

        num_lines_out = sum(1 for line in open(output_file_path))
        num_lines_out_formatted = "{:,}".format(num_lines_out)

        num_lines_diff = num_lines_original - num_lines_out
        num_lines_diff_formatted = "{:,}".format(num_lines_diff)

        self.stdout.write(f"Output #lines {num_lines_out_formatted}")

        self.stdout.write(f"Saved  #lines {num_lines_diff_formatted}")

        self.stdout.write(self.style.WARNING("\nItem types of interest -------------"))
        type_list = ", ".join(item_types)
        self.stdout.write(f"\n[{type_list}]")

        self.stdout.write(self.style.WARNING("\nItem statuses -------------"))
        status_list = ", ".join(item_statuses)
        self.stdout.write(f"\n[{status_list}]")

        # stats to file
        stats_filename = generate_stats_file(file_path, type_stats)
        self.stdout.write(self.style.SUCCESS(f"\nStats file is here: {stats_filename}"))

        self.stdout.write(
            self.style.SUCCESS(f"\nFinished Your file is here: {output_file_name}")
        )
