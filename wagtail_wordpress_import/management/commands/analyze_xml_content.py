import collections
import json
import re

from django.core.management.base import BaseCommand
from lxml import etree


class Command(BaseCommand):

    help = """Utils to output xml structure to a json file."""

    # def __init__(self, *args, **kwargs):
    #     # self.xml_folder_path = "xml"
    #     # self.json_folder_path = "json"
    #     if not os.path.exists(self.json_folder_path):
    #         os.makedirs(self.json_folder_path)
    #     super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument("xmlfile", type=str)

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Parsing ..."))
        self.stdout.write(
            self.style.NOTICE(
                "If this is a large file and has many depths it will take some time to complete"
            )
        )
        file_name = options["xmlfile"]
        xml = open(file_name, "rb").read()

        json_file_name = file_name.split(".")[0]
        json_file = open(f"{json_file_name}.json", "w+")

        paths_dict = PathsToDict(xml).get_dict()

        json_file.write(json.dumps(paths_dict, indent=2))

        self.stdout.write(
            self.style.SUCCESS(f"Finished Your file is here: {json_file_name}.json")
        )


class PathsToDict:
    """
    Flatten the xml file tree.

    ...

    This is used when running the discovery command. The output has no original
    data and keys are xml tags and values are xml tag attribute names,
    genrated form the json file

    Attributes
    ----------
    xml_file: str
        the raw string xml file

    Methods
    -------
    get_dict()
        Traverse the xml tree.
        Check if the max_depth has been reached and if so stop and return
        a dict that represents all the unique tags of the xml file including
        attribute names

        Return collections.OrderedDict()

    """

    def __init__(self, xml_file):
        """
        Parameters
        ----------

        current_depth : int
            to keep track of the current depth during parsing
        max_depth : int
            the number of the deepest xml tags (tree)
        xml_root : lxml.etree
            the xml parsed and which we loop through
        raw_tree : str
            used when converting a tag to str representaion

        """
        self.current_depth = 0
        self.max_depth = MaxDepthEtree(xml_file)
        self.xml_root = etree.fromstring(xml_file)
        self.raw_tree = etree.ElementTree(self.xml_root)

    @staticmethod
    def get_path(tag, raw_tree):
        """
        Return a string: output a string like, /catalog/book/description
        from the tag path
        """

        return re.sub(r"\[[0-9]+\]", "", raw_tree.getpath(tag))

    @staticmethod
    def set_current_depth(path):
        """
        Count the current parts of path
        e.g. /catalog/book/description = 3
        """

        return len(str(path).strip("/").split("/"))

    @staticmethod
    def set_attrs(tag):
        """
        Extract any attribute names of a path
        """

        return ",".join([attr for attr in tag.keys()])

    def get_dict(self):
        """
        Traverse the xml tree
        """

        nice_tree = collections.OrderedDict()
        counter = 0

        for tag in self.xml_root.iter():
            counter += 1
            # out = f"({counter}) ... {tag}\n"
            # sys.stdout.write(out)
            path = self.get_path(tag, self.raw_tree)
            current_depth = self.set_current_depth(path)
            max_depth_reached = current_depth == self.max_depth

            if path in nice_tree and max_depth_reached:
                break

            if path not in nice_tree:
                nice_tree[path] = []

            if len(tag.keys()) > 0:
                nice_tree[path] = self.set_attrs(tag)

        return nice_tree


class MaxDepthEtree:
    """
    Calculate the maximum depth of an xml file tree.

    ...

    Traversing the tree until the root element is reached

    Attributes
    ----------
    xml : str
        the raw xml file

    Methods
    -------
    get_depth()
        Returns the calculated max depth of the xml file

    """

    def __init__(self, xml):
        """
        Parameters
        -----------

        max_depth : int
            keep track of the deepest so far
        tree : the xml tree to parse

        """
        self.max_depth = 0
        self.tree = etree.ElementTree(etree.fromstring(xml))

    def _depth(self, elem, level):
        """
        Recursive method to count the current depth
        """

        if level == self.max_depth:
            self.max_depth += 1
        for child in elem:
            self._depth(child, level + 1)

    def get_depth(self):
        """
        # returning 1 greater than actual length to work with
        """
        self._depth(self.tree.getroot(), -1)
        return self.max_depth + 1
