import collections
import re
import sys
from datetime import datetime
from xml.dom import pulldom

from django.apps import apps
from django.utils.timezone import make_aware
from lxml import etree
from wagtail.core.models import Page

from wagtail_xmlimport.functions import node_to_dict

# TODO put in a better place as extending the PageBuilder may need different
# date function


def process_date(datestring):
    return make_aware(datetime.strptime(datestring, "%Y-%m-%dT%H:%M:%S"))


# TODO: a bteer for sure
def reset_updated_dates(obj, date, revision):
    # update the dates
    obj.first_published_at = date
    obj.last_published_at = date
    obj.latest_revision_created_at = date
    obj.save()
    # rev = obj.save_revision()
    revision.publish()


class ImportXml:

    XML_DIR = "xml"
    # we may need to modify this going forward (multisite?)

    def __init__(self, mapping):
        self.SITE_ROOT_PAGE = Page.get_first_root_node().get_children().first()
        self.mapping = mapping
        self.imported_items = []
        self.mapping_meta = self.mapping.get("root")
        self.set_xml_file_path()

    def set_xml_dir(self, folder_path="xml"):
        self.XML_DIR = folder_path

    def set_json_folder(self, folder_path="json"):
        self.JSON_DIR = folder_path

    def set_xml_file_path(self):
        xml_folder = self.XML_DIR
        xml_file_name = self.mapping_meta.get("file")[0]
        self.full_xml_path = f"{xml_folder}/{xml_file_name}"

    def run_import(self):
        tag = self.mapping_meta.get("tag")[0]
        model = self.mapping_meta.get("model")[0]
        xml_doc = pulldom.parse(self.full_xml_path)
        for event, node in xml_doc:

            if event == pulldom.START_ELEMENT and node.tagName == tag:
                xml_doc.expandNode(node)
                dict = node_to_dict(node)
                page = PageBuilder(dict, model, self.mapping, self.SITE_ROOT_PAGE)

                if page:
                    dict["result"] = page.result
                    self.imported_items.append(dict)

        return self.imported_items


class PageBuilder:
    def __init__(self, item, model, mapping, site_root_page):
        self.item = item
        self.model = model
        self.mapping = mapping
        self.values = {}
        self.site_root_page = site_root_page
        self.date_field_value = None
        result = self.parse_item(self.model, self.item, self.mapping)
        self.result = result

    def parse_item(self, model, item, mapping):
        # required_fields = []
        self.page_model = apps.get_model("pages", model)
        for key in mapping.keys():
            if isinstance(mapping[key], list) and len(mapping[key]) >= 1:
                if mapping[key][0] == "*date":
                    self.date_field_value = process_date(
                        "T".join(item.get(key).split(" "))
                    )
                page_data = item.get(key)
                # may need to make list of required fields and save
                # to validate before page is made + logging the issue
                if (
                    len(mapping[key]) > 1
                    and mapping[key][-1] == "required"
                    and not page_data
                ):
                    return  # for now just return
                if len(mapping[key]) >= 1 and not mapping[key][-1] == "*date":
                    k = mapping[key][0]
                    self.values[k] = page_data

        page_exists = self.page_model.objects.filter(
            wp_post_id=self.values.get("wp_post_id")
        ).first()

        if not page_exists:
            page_id, result = self.make_page(self.page_model)
            return page_id, result

        page_id_updated, result = self.update_page(page_exists.id)
        return page_id_updated, result

    def make_page(self, page_model):
        obj = page_model(**self.values)
        self.site_root_page.add_child(instance=obj)
        rev = obj.save_revision()
        rev.publish()
        if self.date_field_value:
            reset_updated_dates(obj, self.date_field_value, rev)

        return obj.id, "created"

    def update_page(self, page_id):
        page = self.page_model.objects.get(pk=page_id)
        keys = [field.name for field in page._meta.get_fields()]
        for key in keys:
            if key in self.values:
                page.key = self.values[key]
        rev = page.save_revision()
        rev.publish()
        if self.date_field_value:
            reset_updated_dates(page, self.date_field_value, rev)

        return page.id, "updated"


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
        max_depth = self.max_depth + 1

        return max_depth


class PathsToDict:
    """
    Flatten the xml file tree.

    ...

    This is used when running the discovery command. The ouput has no original
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
            out = f"({counter}) ... {tag}\n"
            sys.stdout.write(out)
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
