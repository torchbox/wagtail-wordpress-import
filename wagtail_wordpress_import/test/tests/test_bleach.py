import os

from django.test import TestCase

from wagtail_wordpress_import.functions import linebreaks_wp
from wagtail_wordpress_import.bleach import bleach_clean, fix_styles

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/test_fixtures"
"""
Sanity checks when file is loaded for testing
Checking the expected count of items is as expected
"""
# original values of loaded fixture
COUNTER_OCCURANCE_TOTAL = 16  #  (xcounterx)
IPSUM_OCCURANCE_TOTAL = 18  #  ipsum
SPAN_OCCURANCE_TOTAL = 8  # <span
LINES_OCCURANCE_TOTAL = 11  # \n\n

# altered values
OUTPUT_DOUBLE_LINES_OCCURANCE_TOTAL = 0  # \n\n
OUTPUT_SINGLE_LINES_OCCURANCE_TOTAL = 20  # \n\n
OUTPUT_P_OCCURANCE_TOTAL = 8  # <p> we already have one in place which shoudl remain


class TestBleach(TestCase):
    def setUp(self):
        self.raw_html_file = open(f"{FIXTURES_PATH}/input_raw.txt", "r")
        self.stream = self.raw_html_file.read()
        # import re
        # self.raw_text = re.sub("<[^<]+?>", "", self.stream)

    def test_loaded_original_file(self):
        self.assertEqual(self.stream.count("(xcounterx)"), COUNTER_OCCURANCE_TOTAL)
        self.assertEqual(self.stream.count("ipsum"), IPSUM_OCCURANCE_TOTAL)
        self.assertEqual(self.stream.count("<span"), SPAN_OCCURANCE_TOTAL)
        self.assertEqual(self.stream.count("\n\n"), LINES_OCCURANCE_TOTAL)

    def test_bleach_clean(self):
        bc = bleach_clean(self.stream)
        self.assertNotIn('onmouseover=alert("Boo!")', bc)

    def test_linebreaks_wp(self):
        lb_wp = linebreaks_wp(self.stream)
        self.assertEqual(lb_wp.count("(xcounterx)"), COUNTER_OCCURANCE_TOTAL)
        self.assertEqual(lb_wp.count("ipsum"), IPSUM_OCCURANCE_TOTAL)
        self.assertEqual(lb_wp.count("<span"), SPAN_OCCURANCE_TOTAL)
        self.assertEqual(lb_wp.count("\n\n"), OUTPUT_DOUBLE_LINES_OCCURANCE_TOTAL)
        self.assertEqual(lb_wp.count("\n"), OUTPUT_SINGLE_LINES_OCCURANCE_TOTAL)
        self.assertEqual(lb_wp.count("<p"), OUTPUT_P_OCCURANCE_TOTAL)

    # def test_fix_styles(self):
    #     value = self.stream
    #     value = linebreaks_wp(value)
    #     value = fix_styles(value)
    #     value = bleach_clean(value)
