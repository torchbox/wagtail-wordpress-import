import os

from django.test import TestCase

from wagtail_wordpress_import.prefilters.bleach_filter import filter_bleach_clean

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/fixtures"


class TestBleach(TestCase):
    def setUp(self):
        self.raw_html_file = open(f"{FIXTURES_PATH}/raw_html.txt", "r")
        self.stream = self.raw_html_file.read()

    def test_bleach_clean(self):
        bc = filter_bleach_clean(self.stream)
        self.assertNotIn('style=" float: left;"', bc)
        self.assertNotIn('onmouseover=alert("Boo!")', bc)
