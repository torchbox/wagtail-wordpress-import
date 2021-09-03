import os
from django.test import TestCase
from wagtail_xmlimport.cls.cls import MaxDepthEtree, PathsToJson
from lxml import etree

FIXTURES_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)



class TestDiscovery(TestCase):
    def setUp(self):
        # this is a 
        self.xml = open(os.path.join(FIXTURES_DIR, "fixtures/test.xml"), "rb").read()
        self.known_depth = 5
        self.xml_root = etree.fromstring(self.xml)
        # self.max_depth_etree = MaxDepthEtree(self.xml)

    def test_max_depth_etree_cls(self):
        max_depth_etree = MaxDepthEtree(self.xml)
        self.assertIsInstance(max_depth_etree, MaxDepthEtree)

        self.max_depth = max_depth_etree.get_depth()
        self.assertEqual(self.max_depth, self.known_depth)

    def test_path_to_json(self):
        paths_dict = PathsToJson(self.xml_root, self.max_depth)
        self.assertEqual(paths_dict.max_depth, self.known_depth)
