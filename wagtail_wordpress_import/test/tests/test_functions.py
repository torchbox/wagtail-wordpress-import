from django.test import TestCase

from wagtail_wordpress_import.functions import get_attr_as_list, snakecase_key


class TestSnakeCaseKey(TestCase):
    def test_snake_case_key_remove_colon(self):
        self.assertEqual(snakecase_key("foo:bar"), "foo_bar")

    def test_snake_case_key_remove_leading_underscore(self):
        self.assertEqual(snakecase_key("_foo_bar"), "foo_bar")


class TestDictToList(TestCase):
    def test_default_with_string(self):
        node = "foo"
        self.assertEqual(get_attr_as_list(node, "foo"), [])

    def test_default_with_dict(self):
        node = {}
        self.assertEqual(get_attr_as_list(node, "foo"), [])

    def test_default_with_list(self):
        node = []
        self.assertEqual(get_attr_as_list(node, "foo"), [])

    def test_default_list(self):
        node = ["foo"]
        self.assertEqual(get_attr_as_list(node, "foo"), [])

    def test_default_empty_dict(self):
        node = {"foo": {}}
        self.assertEqual(get_attr_as_list(node, "foo"), [])

    def test_with_expected_dict(self):
        node = {"foo": {"bar": "baz", "baz": "bar"}}
        self.assertEqual(get_attr_as_list(node, "foo"), [{"bar": "baz", "baz": "bar"}])

    def test_with_expected_list(self):
        node = {"foo": [{"bar": "baz", "baz": "bar"}]}
        self.assertEqual(get_attr_as_list(node, "foo"), [{"bar": "baz", "baz": "bar"}])
