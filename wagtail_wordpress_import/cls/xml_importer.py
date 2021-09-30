""" here only as reminder for earlier code will be removed"""

from xml.dom import pulldom

from wagtail.core.models import Page
from wagtail_wordpress_import.cls.page_builder import PageBuilder
from wagtail_wordpress_import.functions import node_to_dict


class XmlImporter:
    # we may need to modify this going forward (multisite?)

    XML_DIR = "xml"

    def __init__(self, map_file):
        # TODO: this is only the default home page just now
        self.SITE_ROOT_PAGE = Page.get_first_root_node().get_children().first()
        self.mapping = map_file
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

    def run_import(self, progress_manager):
        """
        There's a correlation between type and models and app below
        The order should match in types, models and apps
        """

        # the item types to import
        types = self.mapping_meta.get("type")
        # the page model for each type
        models = self.mapping_meta.get("model")
        # the wagtail apps where the page models are located
        apps = self.mapping_meta.get("app")

        if not len(types) == len(models):
            exit(
                """Types and models should contain the same number of items and should be in the same order for the relation to each other. e.g. ['page', 'posts'] and ['PagePage', 'PostPage']"""
            )

        """all looks good lets go"""
        self.progress_manager = progress_manager

        # the key that holds the value for types below
        type_key = self.mapping_meta.get("key")[0]

        # the xml tag that defines all items
        tag = self.mapping_meta.get("tag")[0]

        to_parse = {
            types[x]: [
                models[x],
                apps[x],
            ]
            for x in range(len(types))
        }  # e.g post(PostPage, pages)

        xml_doc = pulldom.parse(self.full_xml_path)

        for event, node in xml_doc:
            # each node represents a tag in the xml
            # event is true for the start element
            if event == pulldom.START_ELEMENT and node.tagName == tag:

                print("⏳ working ...", end="\r")
                xml_doc.expandNode(node)
                dict = node_to_dict(node)

                if dict.get(type_key) in to_parse:
                    # to each item pass the type, model & app
                    tag_type = dict.get(type_key)
                    tag_model = to_parse[tag_type][0]
                    tag_app = to_parse[tag_type][1]

                    self.progress_manager.processed.append(dict)

                    # TODO: could do with making these params clearer
                    builder = PageBuilder(
                        dict,
                        tag_model,
                        self.mapping,
                        self.SITE_ROOT_PAGE,
                        self.progress_manager,
                        tag_type,
                        tag_app,
                    )

                    result = builder.run()

                    if result:
                        print(result)

        return True
