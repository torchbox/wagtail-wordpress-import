import os
import json
from django.test import TestCase
from datetime import datetime
from wagtail_wordpress_import.importers.wordpress import WordpressItem
from wagtail_wordpress_import.logger import Logger

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/fixtures"


class WordpressItemTests(TestCase):
    def setUp(self):
        self.logger = Logger("fakedir")
        raw_html_file = open(f"{FIXTURES_PATH}/raw_html.txt", "r").read()
        self.good_node = {
            "title": "Page Title",
            "wp:post_name": "page-title",
            "wp:post_date_gmt": "2017-03-12 17:53:57",
            "wp:post_modified_gmt": "2018-12-04 11:49:24",
            "content:encoded": raw_html_file,
            "wp:post_id": "1000",
            "wp:post_type": "post",
            "link": "http://www.example.com",
        }
        self.bad_node = {
            "title": "Page Title",
            "wp:post_name": "",
            "wp:post_date_gmt": "0000-00-00 00:00:00",
            "wp:post_modified_gmt": "0000-00-00 00:00:00",
            "content:encoded": raw_html_file,
            "wp:post_id": "1000",
            "wp:post_type": "post",
            "link": "",
        }

    def test_all_fields_with_good_data(self):
        wordpress_item = WordpressItem(self.good_node, self.logger)
        title = wordpress_item.cleaned_data["title"]
        slug = wordpress_item.cleaned_data["slug"]
        first_published_at = wordpress_item.cleaned_data["first_published_at"]
        last_published_at = wordpress_item.cleaned_data["last_published_at"]
        latest_revision_created_at = wordpress_item.cleaned_data[
            "latest_revision_created_at"
        ]
        body = wordpress_item.cleaned_data["body"]
        wp_post_id = wordpress_item.cleaned_data["wp_post_id"]
        wp_post_type = wordpress_item.cleaned_data["wp_post_type"]
        wp_link = wordpress_item.cleaned_data["wp_link"]
        wp_raw_content = wordpress_item.debug_content["filter_linebreaks_wp"]
        wp_processed_content = wordpress_item.debug_content["filter_fix_styles"]
        wp_block_json = wordpress_item.debug_content["block_json"]

        self.assertEqual(title, "Page Title")
        self.assertEqual(slug, "page-title")
        self.assertIsInstance(first_published_at, datetime)
        self.assertIsInstance(last_published_at, datetime)
        self.assertIsInstance(latest_revision_created_at, datetime)
        self.assertIsInstance(json.dumps(body), str)
        self.assertEqual(wp_post_id, 1000)
        self.assertEqual(wp_post_type, "post")
        self.assertEqual(wp_link, "http://www.example.com")
        self.assertIsInstance(wp_raw_content, str)
        self.assertIsInstance(wp_processed_content, str)
        self.assertIsInstance(wp_block_json, list)

    def test_cleaned_fields(self):
        wordpress_item = WordpressItem(self.bad_node, self.logger)
        slug = wordpress_item.cleaned_data["slug"]
        first_published_at = wordpress_item.cleaned_data["first_published_at"]
        last_published_at = wordpress_item.cleaned_data["last_published_at"]
        latest_revision_created_at = wordpress_item.cleaned_data[
            "latest_revision_created_at"
        ]
        wp_link = wordpress_item.cleaned_data["wp_link"]
        self.assertEqual(slug, "page-title")
        self.assertIsInstance(first_published_at, datetime)
        self.assertIsInstance(last_published_at, datetime)
        self.assertIsInstance(latest_revision_created_at, datetime)
        self.assertEqual(wp_link, "")
