import json
from datetime import datetime
from django.test import TestCase
from wagtail_xmlimport.importers import wordpress_mapping
from wagtail_xmlimport.importers.wordpress import WordpressImporter


class ImpoterTests(TestCase):

    def setUp(self):
        self.imp = WordpressImporter("fakexml.xml")

    def test_wordpress_mapping(self):
        mapping = wordpress_mapping.mapping
        self.assertIsInstance(mapping, dict)

    def test_importer_class(self):
        self.assertIsInstance(self.imp, WordpressImporter)

    def test_importer_init(self):
        self.assertEqual(self.imp.xml_file, "fakexml.xml")
        self.assertIsInstance(self.imp.mapping, dict)
        self.assertEqual(
            self.imp.mapping_valid_date,
            "first_published_at,last_published_at,latest_revision_created_at",
        )
        self.assertEqual(self.imp.mapping_valid_slug, "slug")
        self.assertEqual(self.imp.mapping_stream_fields, "body")
        self.assertEqual(self.imp.log_processed, 0)
        self.assertEqual(self.imp.log_imported, 0)
        self.assertEqual(self.imp.log_skipped, 0)
        self.assertIsInstance(self.imp.logged_items, list)

    def test_map_item_inverse(self):
        inv = self.imp.map_item_inverse()
        self.assertEqual(inv.get("slug"), "wp:post_name")
        
    def test_parse_date(self):
        bad_date = self.imp.parse_date("0000-00-00 00:00:00")
        self.assertIsInstance(bad_date[0], datetime)
        good_date = self.imp.parse_date("2010-07-13 12:16:46")
        self.assertIsInstance(good_date[0], datetime)

    def test_parse_slug(self):
        good_slug = self.imp.parse_slug("good-slug", "Good Slug Passed Here")
        self.assertEqual(good_slug[0], "good-slug")
        self.assertEqual(good_slug[1], "OK")
        bad_slug = self.imp.parse_slug("page%2&e-#ti#tle", "Bad Slug Passed Here")
        self.assertEqual(bad_slug[0], "page2e-title")
        self.assertEqual(bad_slug[1], "illegal chars found")
        blank_slug = self.imp.parse_slug("", "Page Without Slug")
        self.assertEqual(blank_slug[0], "page-without-slug")
        self.assertEqual(blank_slug[1], "blank slug")

    def test_parse_stream_fields(self):
        blocks = self.imp.parse_stream_fields("A line without a tag")
        self.assertIsInstance(blocks, str)
        blocks_dict = json.loads(blocks)
        self.assertEqual(blocks_dict[0]["type"], "raw_html")
        # new line added by linebreaks_wp function
        self.assertEqual(blocks_dict[0]["value"], "<p>A line without a tag</p>\n")

    def test_get_values(self):
        body = """&lt;strong&gt;Pipe down over there, I'm about to tell ya ;)&lt;/strong&gt; 
        The lucky winner of the &lt;a href="https://www.budgetsaresexy.com/2012/12/christmas-stimulus-amazon-shopping-spree-giveaway/"&gt;4th 
        Annual Christmas Stimulus 2012&lt;/a&gt; presented by J. Money and Brad Chaffee, and who will be receiving $200 smackers to Amazon this 
        year is.... and who also better buy his/her mom something nice for bringing him/her INTO this world of ours is.... bum bum bum.... 
        Hey, when was the last time I you a joke? Have you ever heard the one about the jump rope? Ahh, never mind just skip it ;)

        Okay okay, the winner of the 200 bones to Amazon, and who will also be treating their significant other to something&#160; 
        nice as well as their mom is... bum bum bum... Hey Roger - do we have any commercial breaks to get into here? No? Okay okay... 
        we'll announce who the winner is finally then.... bum bum&#160; bum... Are you ready?&#160; 
        Will it be you? Well, we're about to find out! The lucky winner of the &lt;em&gt;4th 
        Annual Christmas Stimulus 2012&lt;/em&gt; presented by J$ and Bradley 
        Chaffee is... bum bum bum... &lt;span style="color: #008000;"&gt;&lt;strong&gt;Ryan Smith&lt;/strong&gt;&lt;/span&gt;! 
        Congrats! Now don't go spending it all in one spot ;)

        Happy holidays everyone, thanks SO MUCH for being a part of our BudgetsAreSexy family!

        &amp;nbsp;"""

        good_values = self.imp.get_values({
            "title": "Page Title",
            "wp:post_name": "page-title",
            "wp:post_date_gmt": "2010-07-13 16:16:46",
            "wp:post_modified_gmt": "2010-07-13 16:16:46",
            "content:encoded": body,
            "wp:post_id": "30531",
            "wp:post_type": "post",
            "link": "https://www.domain.com/page-title/",
        })

        self.assertIsInstance(good_values, tuple)
        self.assertTrue(good_values[1])
        self.assertTrue(good_values[2])

        bad_date_values = self.imp.get_values({
            "title": "Page Title",
            "wp:post_name": "page-title",
            "wp:post_date_gmt": "0000-00-00 00:00:00",
            "wp:post_modified_gmt": "2010-07-13 16:16:46",
            "content:encoded": body,
            "wp:post_id": "30531",
            "wp:post_type": "post",
            "link": "https://www.domain.com/page-title/",
        })

        self.assertIsInstance(bad_date_values, tuple)
        self.assertFalse(bad_date_values[1])
        self.assertTrue(bad_date_values[2])
        
        missing_slug_values = self.imp.get_values({
            "title": "Page Title",
            "wp:post_name": "",
            "wp:post_date_gmt": "2010-07-13 16:16:46",
            "wp:post_modified_gmt": "2010-07-13 16:16:46",
            "content:encoded": body,
            "wp:post_id": "30531",
            "wp:post_type": "post",
            "link": "https://www.domain.com/page-title/",
        })

        self.assertIsInstance(missing_slug_values, tuple)
        self.assertEqual(missing_slug_values[2], "blank slug")
