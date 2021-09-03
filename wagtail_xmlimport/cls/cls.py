import re, collections
from lxml import etree

class MaxDepthEtree():
    def __init__(self, xml):
        self.maxdepth = 0
        self.tree = etree.ElementTree(etree.fromstring(xml))

    def depth(self, elem, level):
        if level == self.maxdepth:
            self.maxdepth += 1
        # recursive call to function to get the depth
        for child in elem:
            self.depth(child, level + 1)

    def get_depth(self):
        # tree = etree.ElementTree(etree.fromstring(xml))
        self.depth(self.tree.getroot(), -1)
        # return 1 greater than actual length to work with
        return self.maxdepth + 1


class PathsToJson():

    def __init__(self, xml_root, max_depth):
        self.max_depth = max_depth
        self.xml_root = xml_root
        self.current_depth = 0
        self.raw_tree = etree.ElementTree(self.xml_root)
        self.nice_tree = collections.OrderedDict()

    def get_path(self, tag):
        return re.sub("\[[0-9]+\]", "", self.raw_tree.getpath(tag))

    def set_current_depth(self, path):
        return len(str(path).strip("/").split("/"))

    def set_attrs(self, tag):
        return ",".join([attr for attr in tag.keys()])

    def get_json(self):
        for tag in self.xml_root.iter():
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