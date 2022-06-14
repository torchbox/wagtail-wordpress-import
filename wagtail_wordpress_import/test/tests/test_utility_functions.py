from django.test import TestCase

from wagtail_wordpress_import.test.tests.utility_functions import (
    get_soup,
    mock_image,
    mock_pdf,
)


class TestFixtures(TestCase):
    def setUp(self):
        self.image = mock_image()
        self.pdf = mock_pdf()

    def test_mock_image(self):
        self.assertEqual(self.image.name, "test.jpg")

    def test_mock_image_content(self):
        image_content = self.image.read()
        self.assertTrue(image_content.startswith(b"\xff\xd8"))

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
