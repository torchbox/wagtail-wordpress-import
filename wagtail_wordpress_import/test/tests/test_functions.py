from django.test import TestCase
from wagtail_wordpress_import.functions import normalize_style_attrs


class TestFuntions(TestCase):
    def test_normalize_style_attrs(self):

        html = normalize_style_attrs(
            """
            <span style="FONT-WEIGHT:BOLD; font-style: italic ">Lorem</span>
            """
        )

        self.assertTrue("font-weight:bold;" in html)
        self.assertTrue("font-style:italic;" in html)
