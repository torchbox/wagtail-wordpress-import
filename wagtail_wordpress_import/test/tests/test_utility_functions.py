from django.test import TestCase
from wagtail_wordpress_import.test.tests.utility_functions import (
    mock_image,
    mock_pdf,
    get_soup,
)


class TestFixtures(TestCase):
    def test_mock_image(self):
        image_content = mock_image().read()
        self.assertTrue(image_content.startswith(b"\x89PNG"))

    def test_mock_pdf(self):
        pdf_content = mock_pdf().read()
        self.assertEqual(pdf_content, b"PDF Document")

    def test_get_soup_html_parser(self):
        soup = get_soup("<p>Hello</p>", "html.parser")
        self.assertEqual(soup.p.text, "Hello")

    def test_get_soup_html5lib(self):
        soup = get_soup("<p>Hello</p>", "html5lib")
        self.assertEqual(soup.p.text, "Hello")

    def test_get_soup_lxml(self):
        soup = get_soup("<p>Hello</p>", "lxml")
        self.assertEqual(soup.p.text, "Hello")
