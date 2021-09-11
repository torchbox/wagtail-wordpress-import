from xml.dom import pulldom

from wagtail.core.models import Page
from wagtail_xmlimport.cls.page_builder import PageBuilder
from wagtail_xmlimport.functions import node_to_dict


class XmlImporter:
    # we may need to modify this going forward (multisite?)

    XML_DIR = "xml"

    def __init__(self, map_file, tag, type, status):
        # TODO: this is only the default home page just now
        self.SITE_ROOT_PAGE = Page.get_first_root_node().get_children().first()
        self.mapping = map_file
        self.mapping_meta = self.mapping.get("root")
        self.set_xml_file_path()
        self.tag = tag
        self.type = type
        self.status = status

    def set_xml_dir(self, folder_path="xml"):
        self.XML_DIR = folder_path

    def set_json_folder(self, folder_path="json"):
        self.JSON_DIR = folder_path

    def set_xml_file_path(self):
        xml_folder = self.XML_DIR
        xml_file_name = self.mapping_meta.get("file")[0]
        self.full_xml_path = f"{xml_folder}/{xml_file_name}"

    def run_import(self, progress_manager):
        # parse all item tags and types in one go in the end
        # pass the post status so we can set the wagtail page status
        self.progress_manager = progress_manager
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
                self.progress_manager.processed.append(dict)

                if dict.get("wp:post_type") == type:
                    
                    builder = PageBuilder(
                        dict, model, self.mapping, self.SITE_ROOT_PAGE, self.progress_manager
                    )
                    result = builder.run()
                    
                    if result:
                        print(result)

        return True
