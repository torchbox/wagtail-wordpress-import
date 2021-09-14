from xml.dom import pulldom
from wagtail_xmlimport.importers import wordpress_mapping
from wagtail_xmlimport.functions import node_to_dict
from wagtail_xmlimport.cls.page_builder import PageBuilder


class WordpressImporter:
    def __init__(self, xml_file_path):
        self.xml_file = xml_file_path
        self.mapping = wordpress_mapping.mapping
        self.mapping_root = self.mapping.get("root")
        self.mapping_item = self.mapping.get("item")

    def run(self, page_type, page_model, parent_page):
        xml_doc = pulldom.parse(self.xml_file)
        tag = self.mapping_root.get("tag")
        print("⏳ working ...", end="\r")
        for event, node in xml_doc:
            # each node represents a tag in the xml
            # event is true for the start element
            if event == pulldom.START_ELEMENT and node.tagName == tag:
                xml_doc.expandNode(node)
                dict = node_to_dict(node)
                
                builder = PageBuilder(
                        dict,
                        page_model,
                        self.mapping,
                        parent_page,
                        self.progress_manager,
                        page_type,
                        "pages",
                    )

                result = builder.run()
                


wordpress_importer_class = WordpressImporter
