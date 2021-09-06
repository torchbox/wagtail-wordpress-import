import collections
import re
import sys

from lxml import etree


class MaxDepthEtree:
    """calculate the maximum depth of an xml tree
    by traversing the tree until the root element is reached"""

    def __init__(self, xml):
        # we return the max_depth
        self.max_depth = 0
        # parse the xml file
        self.tree = etree.ElementTree(etree.fromstring(xml))

    def depth(self, elem, level):
        if level == self.max_depth:
            self.max_depth += 1
        # recursive call to get the current depth
        for child in elem:
            self.depth(child, level + 1)

    def get_depth(self):
        # returning 1 greater than actual length to work with
        self.depth(self.tree.getroot(), -1)
        return self.max_depth + 1


class PathsToDict:
    """flatten the xml tree as a dict.
    The current depth is tracked and when the depth is less than
    the max_depth we can stop"""

    def __init__(self, xml_root, max_depth, progress=True):
        self.max_depth = max_depth
        self.xml_root = xml_root
        self.current_depth = 0
        self.raw_tree = etree.ElementTree(self.xml_root)
        self.nice_tree = collections.OrderedDict()
        self.progress = progress

    def get_path(self, tag):
        # output a string like, /catalog/book/description
        # from the tag path
        return re.sub("\[[0-9]+\]", "", self.raw_tree.getpath(tag))

    def set_current_depth(self, path):
        # how many parts to path used later to determine
        # if max depth has been reached
        return len(str(path).strip("/").split("/"))

    def set_attrs(self, tag):
        # return any attributes of a path whcih may be useful
        return ",".join([attr for attr in tag.keys()])

    def get_dict(self):
        # looking for if the max_depth has been reached and if so
        # stop traversing the tree and retun the result
        for tag in self.xml_root.iter():
            # if self.progress:
            #     print(".")
            path = self.get_path(tag)
            current_depth = self.set_current_depth(path)
            max_depth_reached = current_depth == self.max_depth

            if path in self.nice_tree and max_depth_reached:
                break

            if path not in self.nice_tree:
                self.nice_tree[path] = []

            if len(tag.keys()) > 0:
                self.nice_tree[path] = self.set_attrs(tag)

        return self.nice_tree
