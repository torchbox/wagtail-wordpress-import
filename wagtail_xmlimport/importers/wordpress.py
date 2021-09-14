from copy import copy
from xml.dom import pulldom
from wagtail_xmlimport.importers import wordpress_mapping
from wagtail_xmlimport.functions import node_to_dict

from wagtail_xmlimport.cls.page_maker import PageMaker
from wagtail_xmlimport.cls.progress import ProgressManager
from django.apps import apps

'''

        '''

class WordpressImporter:
    def __init__(self, xml_file_path):
        self.xml_file = xml_file_path
        self.mapping = wordpress_mapping.mapping
        self.mapping_root = self.mapping.get("root")
        self.mapping_item = self.mapping.get("item")
        self.progress_manager = ProgressManager()

    def run(self, *args, **kwargs):
        xml_doc = pulldom.parse(self.xml_file)
        tag = self.mapping_root.get("tag")
        self.page_model_instance = apps.get_model(
            kwargs["app_for_pages"], kwargs["model_for_pages"]
        )
        self.parent_page_obj = (
            apps.get_model(kwargs["app_for_parent"], kwargs["model_for_parent"])
            .get_first_root_node()
            .get_children()
            .first()
        )
        # print(self.parent_page_model)
        # self.parent_page_obj = apps.get_model(
        # self.parent_page_model.get_first_root_node().get_children().first()
        # )

        print("⏳ working ...", end="\r")

        for event, node in xml_doc:
            # each node represents a tag in the xml
            # event is true for the start element
            if event == pulldom.START_ELEMENT and node.tagName == tag:
                xml_doc.expandNode(node)
                complete_dict = node_to_dict(node)
                
                if complete_dict.get("wp:post_type") and complete_dict.get(
                    "wp:post_type"
                ) == self.mapping_root.get("type"):
                    item_dict = self.get_values(complete_dict)

                    # print(item_dict)
                # exit()
                # exit()
                    self.make_page(item_dict, complete_dict.get("wp:status"))

                # builder = PageMaker(
                #         item_dict,
                #         page_model_instance,
                #         self.mapping_item,
                #         parent_page_obj,
                #         self.progress_manager,
                #         page_type,
                #         "pages",
                #     )

                # result = builder.run()

    def make_page(self, values, status):

        print(values)
        exit()
        
        obj = self.page_model_instance(**values)

        if status == "draft":
            setattr(obj, "live", False)
        else:
            setattr(obj, "live", True)

        self.parent_page_obj.add_child(instance=obj)

        # self.progress_manager.log_page_action(obj, "created")

        return obj, "created"

    def get_values(self, item_dict):

        field_values = {}

        for key in self.mapping_item.keys():
            item_value = item_dict.get(key)
            if isinstance(self.mapping_item.get(key), list):
                for f in range(len(self.mapping_item.get(key))):
                    field_values[self.mapping_item.get(key)] = item_value
            else:
                field_values[self.mapping_item.get(key)] = item_value

            # print(is_list)
            # if type(self.mapping_item[key]) == 'list':
                # TODO: a list of fields to receive the same value
                # for f in self.mapping_item.get(key):
                #     field_values[self.mapping_item.get(key)] = item_value
                # print('list')
                # pass
            # else:
            # item_value = item_dict.get(key)
            #     field_values[self.mapping_item.get(key)] = item_value
        
        return field_values


wordpress_importer_class = WordpressImporter
