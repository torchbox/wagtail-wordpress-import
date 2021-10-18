import os

from bs4 import BeautifulSoup
from django.test import TestCase
from wagtail_wordpress_import.prefilters.linebreaks_wp_filter import (
    filter_linebreaks_wp,
)

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/fixtures"


class TestLinebreaks(TestCase):
    def setUp(self):
        self.raw_html_file = open(f"{FIXTURES_PATH}/raw_text.txt", "r")
        self.stream = self.raw_html_file.read()
        self.soup = BeautifulSoup(filter_linebreaks_wp(self.stream), "html.parser")

    def test_linebreaks_wp(self):
        p_tags = self.soup.findAll("p")
        self.assertEqual(len(p_tags), 7)
