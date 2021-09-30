from django.test import TestCase
from wagtail_wordpress_import.block_builder import check_image_src

class TestBlockBuilder(TestCase):

    def test_check_image_src(self):
        src1 = "https://www.budgetsaresexy.com/folder/myimage.gif"
        src2 = "folder/myimage.gif"

        self.assertEqual(check_image_src(src1), "https://www.budgetsaresexy.com/folder/myimage.gif")
        self.assertEqual(check_image_src(src2), "https://www.budgetsaresexy.com/folder/myimage.gif")
