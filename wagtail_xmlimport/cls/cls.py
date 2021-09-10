import collections
import json
import re
import sys
from datetime import date, datetime
from xml.dom import pulldom

from django.apps import apps
from django.core.validators import validate_slug
from django.utils.text import slugify
from django.utils.timezone import make_aware
from lxml import etree
from wagtail.core.models import Page

from wagtail_xmlimport.functions import node_to_dict, linebreaks_wp

# TODO put in a better place as extending the PageBuilder may need different
# date function

"""
A report from ./manage.py reduce
Original #lines 2,695,253
Output #lines 799,542
Saved #1,895,711 lines
Item types of interest -------------
[attachment, nav_menu_item, custom_css, page, post, tve_lead_group, tve_form_type, tve_lead_shortcode, tve_lead_1c_signup, tve_lead_2s_lightbox]
Item statuses -------------
[inherit, publish, draft, trash, private]
"""


def process_date(datestring):
    return make_aware(datetime.strptime(datestring, "%Y-%m-%dT%H:%M:%S"))


# TODO: doesn't seem right that this needs to happen
# how can save on firt save?
def reset_dates(obj, values, revision):
    # update the dates
    obj.first_published_at = values.get("first_published_at")
    obj.last_published_at = values.get("last_published_at")
    obj.latest_revision_created_at = values.get("latest_revision_created_at")
    obj.save()
    revision.publish()


class ImportXml:

    XML_DIR = "xml"
    # we may need to modify this going forward (multisite?)

    def __init__(self, *args, **kwargs):
        # TODO: this is only the default home page just now
        self.SITE_ROOT_PAGE = Page.get_first_root_node().get_children().first()
        self.mapping = kwargs["map_file"]
        self.imported_items = []
        self.failed_items = []
        self.mapping_meta = self.mapping.get("root")
        self.set_xml_file_path()
        self.tag = kwargs["tag"]
        self.type = kwargs["type"]
        self.status = kwargs["status"]

    def set_xml_dir(self, folder_path="xml"):
        self.XML_DIR = folder_path

    def set_json_folder(self, folder_path="json"):
        self.JSON_DIR = folder_path

    def set_xml_file_path(self):
        xml_folder = self.XML_DIR
        xml_file_name = self.mapping_meta.get("file")[0]
        self.full_xml_path = f"{xml_folder}/{xml_file_name}"

    def run_import(self):
        # parse all item tags and types in one go in the end
        # pass the post status so we can set the wagtail page status
        if self.tag:
            tag = self.tag
        else:
            tag = self.mapping_meta.get("tag")[0]

        if self.type:
            type = self.type
        else:
            type = self.mapping_meta.get("type")[0]

        model = self.mapping_meta.get("model")[0]
        xml_doc = pulldom.parse(self.full_xml_path)

        for event, node in xml_doc:

            if event == pulldom.START_ELEMENT and node.tagName == tag:
                print("⏳ working ...", end="\r")
                xml_doc.expandNode(node)
                dict = node_to_dict(node)
                if dict.get("wp:post_type") == type:
                    
                    builder = PageBuilder(
                        dict, model, self.mapping, self.SITE_ROOT_PAGE
                    )
                    result = builder.run()
                    # see some feedback
                    # print(result)
                    if result:
                        print(result)

                    # if result:
                    #     self.imported_items.append(result[0])

                    # if isinstance(result[0], PagePage):
                    #     self.imported_items.append(result[0])
                    # else:
                    #     self.failed_items.append([dict])

        return self.imported_items, self.failed_items


class PageFieldValueParser:
    def parse_field_value(self, field_name, value, other=None, extra_fields=None):
        if field_name == "title":
            return self.parse_title(value, other)

        if field_name == "body":
            return self.parse_body(value, other)

        if field_name == "wp_post_id":
            return self.parse_wp_post_id(value, other)

        if field_name == "wp_post_type":
            return self.parse_wp_post_type(value, other)

        if field_name == "slug":
            return self.parse_body(value, other)

        if field_name == "date":
            return self.parse_date(value, other, extra_fields)

        if field_name == "status":
            print(value)
            # return self.parse_date(value, other, extra_fields)

    def parse_title(self, value, other):
        if other == "required" and not value:
            return None
        return value

    def parse_body(self, value, other):
        if "body" in other:
            return self.make_stream_blocks(value, other)

    def parse_wp_post_id(self, value, other):
        return value

    def parse_wp_post_type(self, value, other):
        return value

    def parse_slug(self, value, other):
        if "slug" in other:
            return slugify(value)

    def parse_date(self, value, other, extra_fields):
        if other == "required" and not value:
            return None
        extra_fields = extra_fields.split(":")
        date = "T".join(value.split(" "))
        date_formatted = make_aware(datetime.strptime(date, "%Y-%m-%dT%H:%M:%S"))
        ret = {}
        for field in extra_fields:
            ret[field] = date_formatted

        return ret

    def make_stream_blocks(self, value, other):
        pipes = []
        if len(other) > 1 and "stream" in other[1]:
            pipes = other[1].split(":")

        if "*auto_p" in pipes:
            value = linebreaks_wp(value)

        blocks = [{"type": "raw_html", "value": value}]
        return json.dumps(blocks)


class PageBuilder:
    def __init__(self, item, model, mapping, site_root_page):
        self.item = item
        self.model = model
        self.mapping = mapping
        self.values = {}
        self.site_root_page = site_root_page

    def run(self):
        # self.result = result
        # statuses = self.mapping.get("root")["status"]
        # if self.item.get("status") not in statuses:
        # page, result = self.parse_item(self.model, self.item, self.mapping)
        return self.parse_item(self.model, self.item, self.mapping)

    def parse_item(self, model, item, mapping):
        self.page_model = apps.get_model("pages", model)

        # mapping keys are json file keys
        # not interested in the root key
        # values of interest are keys of length > 0
        # we only need to parse items that have one of the statuses

        for key in mapping.keys():

            if isinstance(mapping[key], list) and len(mapping[key]):
                # are there any required fields without a value?
                # don't continue
                if "required" in mapping[key] and not item[key]:
                    continue

                # handle meta like status
                if "__" in mapping[key][0] and mapping[key][0].index("__") == 0:
                    if mapping[key][0] == "__status":
                        self.status = item.get(key)

                # handle everything expect dates and page meta like status
                if not "%%" in mapping[key][0] and not "__" in mapping[key][0]:
                    field_value_parser = PageFieldValueParser()
                    item_value = field_value_parser.parse_field_value(
                        field_name=mapping[key][0],
                        value=item.get(key),
                        other=mapping[key],
                    )
                    self.values[mapping[key][0]] = item_value

                # handle dates
                if "%%" in mapping[key][0] and mapping[key][0].index("%%") == 0:
                    # deal with dates
                    field_value_parser = PageFieldValueParser()
                    extra_fields = None
                    if len(mapping[key]) == 2:
                        extra_fields = mapping[key][1]
                    item_value = field_value_parser.parse_field_value(
                        field_name=mapping[key][0].replace("%%", ""),
                        value=item.get(key),
                        other=False,
                        extra_fields=extra_fields,
                    )

                    for k, v in item_value.items():
                        self.values[k] = v

        if self.status in self.mapping["root"]["status"]:

            page_exists = self.page_model.objects.filter(
                wp_post_id=self.values.get("wp_post_id")
            ).first()

            if not page_exists:
                page, result = self.make_page()
                return page, result

            page, result = self.update_page(page_exists)
            return page, result

    def make_page(self):
        obj = self.page_model(**self.values)

        self.site_root_page.add_child(instance=obj)

        obj.save()
        rev = obj.save_revision()
        rev.publish()

        reset_dates(obj, self.values, rev)

        if self.status == "draft":
            obj.unpublish()

        return obj, "created"

    def update_page(self, page):
        obj = self.page_model.objects.get(pk=page)

        for key in self.values.keys():
            setattr(obj, key, self.values[key])

        obj.save()
        rev = obj.save_revision()

        reset_dates(obj, self.values, rev)

        if self.status == "draft":
            obj.unpublish()
        else:
            rev.publish()

        return obj, "updated"


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
