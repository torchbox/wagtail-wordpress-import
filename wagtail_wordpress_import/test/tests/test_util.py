import os

from django.test import TestCase
from lxml import etree

from wagtail_wordpress_import.cls.util import MaxDepthEtree, PathsToDict

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/fixtures"


class TestDiscovery(TestCase):
    def setUp(self):
        # a known file for testing with
        self.xml = open(os.path.join(FIXTURES_PATH, "test.xml"), "rb").read()
        # we know the max depth is 5 from the file above
        self.known_depth = 3
        # load the xml file
        self.xml_root = etree.fromstring(self.xml)

    def test_max_depth_etree_class_available(self):
        max_depth_etree = MaxDepthEtree(self.xml)
        # is MaxDepthEtree available
        self.assertIsInstance(max_depth_etree, MaxDepthEtree)

        max_depth = max_depth_etree.get_depth()
        # do we get the correct depth for the test xml file
        self.assertEqual(max_depth, self.known_depth)

    def test_paths_to_dict_class_available(self):
        paths_to_dict = PathsToDict(self.xml)
        # is PathsToDict available
        self.assertIsInstance(paths_to_dict, PathsToDict)
        # do we get an instance of dict returned
        self.assertIsInstance(paths_to_dict.get_dict(), dict)
