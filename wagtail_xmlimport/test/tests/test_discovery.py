import collections
import os

from django.test import TestCase
from lxml import etree

from wagtail_xmlimport.cls.cls import MaxDepthEtree, PathsToDict

FIXTURES_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


class TestDiscovery(TestCase):
    def setUp(self):
        # this is a known file for testing
        self.xml = open(os.path.join(FIXTURES_DIR, "fixtures/test.xml"), "rb").read()
        # we know the max depth is 5 from the file above
        self.known_depth = 3
        # load the xml file
        self.xml_root = etree.fromstring(self.xml)

    def test_max_depth_etree_class_available(self):
        max_depth_etree = MaxDepthEtree(self.xml)
        self.assertIsInstance(max_depth_etree, MaxDepthEtree)

        max_depth = max_depth_etree.get_depth()
        self.assertEqual(max_depth, self.known_depth)

    def test_path_to_json_class_available(self):
        max_depth_etree = MaxDepthEtree(self.xml)
        max_depth = max_depth_etree.get_depth()
        paths_to_json = PathsToDict(self.xml_root, max_depth)
        self.assertIsInstance(paths_to_json, PathsToDict)
        # init
        self.assertEqual(paths_to_json.max_depth, self.known_depth)
        self.assertIsNotNone(paths_to_json.xml_root)
        self.assertEqual(paths_to_json.current_depth, 0)
        self.assertTrue("lxml.etree" in str(paths_to_json.raw_tree.__class__))
        self.assertIsInstance(paths_to_json.nice_tree, collections.OrderedDict)
        # get_json
        self.assertIsInstance(paths_to_json.get_dict(), dict)
