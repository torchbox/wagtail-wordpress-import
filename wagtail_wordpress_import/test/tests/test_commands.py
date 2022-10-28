import os

from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

try:
    from wagtail.models import Page
except ImportError:
    from wagtail.core.models import Page

from wagtail_wordpress_import.management.commands.reduce_xml import Command as ReduceCmd
from wagtail_wordpress_import.management.commands.reduce_xml import generate_stats_file
from wagtail_wordpress_import.xml_boilerplate import (
    build_xml_stream,
    generate_temporary_file,
)

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/fixtures"


class TestImportXmlCommandNoConfig(TestCase):
    def test_without_arguments(self):
        with self.assertRaises(CommandError) as ctx:
            call_command("import_xml")
        self.assertEqual(
            str(ctx.exception),
            "Error: the following arguments are required: xml_file, parent_id",
        )

    def test_with_only_xml_file_argument(self):
        with self.assertRaises(CommandError) as ctx:
            call_command("import_xml", "test.xml")
        self.assertEqual(
            str(ctx.exception),
            "Error: the following arguments are required: parent_id",
        )

    def test_with_required_arguments(self):
        with self.assertRaises(SystemExit):
            call_command("import_xml", "test.xml", "2")


@override_settings(
    WAGTAIL_WORDPRESS_IMPORTER_SOURCE_DOMAIN="http://www.example.com",
)
class TestImportXmlCommandWithConfig(TestCase):
    def test_xml_file_error(self):
        # The XML file does not exist
        with self.assertRaises(SystemExit):
            call_command("import_xml", "test.xml", "2")

    def test_run_with_xml_and_parent_id(self):
        built_file = generate_temporary_file(
            build_xml_stream(xml_tags_fragment="").read()
        )

        with self.assertRaises(FileNotFoundError):
            # In testing there is no log folder
            # the command should raise this as an error
            call_command(
                "import_xml",
                built_file,
                "2",
                "-a",
                "wagtail_wordpress_import_test",
                "-m",
                "TestPage",
            )


@override_settings(
    WAGTAIL_WORDPRESS_IMPORTER_SOURCE_DOMAIN="http://www.example.com",
)
class TestImportXmlCommandCompletes(TestCase):

    fixtures = [
        f"{FIXTURES_PATH}/dump.json",
    ]

    def test_run_import_xml(self):
        fragment = """
        <item>
            <title>A title</title>
            <link>https://www.example.com/a-title</link>
            <description />
            <content:encoded />
            <excerpt:encoded />
            <wp:post_id>44221</wp:post_id>
            <wp:post_date>2015-05-21 15:00:31</wp:post_date>
            <wp:post_date_gmt>2015-05-21 19:00:31</wp:post_date_gmt>
            <wp:post_modified>2015-05-21 15:00:44</wp:post_modified>
            <wp:post_modified_gmt>2015-05-21 19:00:44</wp:post_modified_gmt>
            <wp:comment_status>open</wp:comment_status>
            <wp:ping_status>closed</wp:ping_status>
            <wp:post_name>a-title</wp:post_name>
            <wp:status>publish</wp:status>
            <wp:post_type>post</wp:post_type>
        </item>
        <item>
            <title>Not imported</title>
            <link>https://www.example.com/a-title</link>
            <description />
            <content:encoded />
            <excerpt:encoded />
            <wp:post_id>44221</wp:post_id>
            <wp:post_date>2015-05-21 15:00:31</wp:post_date>
            <wp:post_date_gmt>2015-05-21 19:00:31</wp:post_date_gmt>
            <wp:post_modified>2015-05-21 15:00:44</wp:post_modified>
            <wp:post_modified_gmt>2015-05-21 19:00:44</wp:post_modified_gmt>
            <wp:comment_status>open</wp:comment_status>
            <wp:ping_status>closed</wp:ping_status>
            <wp:post_name>a-title</wp:post_name>
            <wp:status>draft</wp:status>
            <wp:post_type>post</wp:post_type>
        </item>
        """
        built_file = generate_temporary_file(
            build_xml_stream(xml_items_fragment=fragment).read()
        )

        with self.assertRaises(FileNotFoundError):
            call_command(
                "import_xml",
                built_file,
                "2",
                "-a",
                "wagtail_wordpress_import_test",
                "-m",
                "TestPage",
                "-t",
                "post",
                "-s",
                "publish",
            )

        parent_page = Page.objects.get(id=2)
        imported_pages = parent_page.get_children().all()
        self.assertEqual(imported_pages.count(), 1)
        self.assertEqual(imported_pages[0].title, "A title")


class TestReduceCommand(TestCase):
    def test_without_arguments(self):
        with self.assertRaises(CommandError) as ctx:
            call_command("reduce_xml")
        self.assertEqual(
            str(ctx.exception),
            "Error: the following arguments are required: xml_file",
        )

    def test_xml_file_error(self):
        # The XML file does not exist
        with self.assertRaises(SystemExit):
            call_command("reduce_xml", "test.xml")

    def test_get_xml_file(self):
        cmd = ReduceCmd()
        with self.assertRaises(SystemExit):
            xml_file = cmd.get_xml_file("test.xml")  # noqa
        with self.assertRaises(SystemExit):
            xml_file = cmd.get_xml_file("folder/test.xml")  # noqa

        built_file = generate_temporary_file(
            build_xml_stream(xml_tags_fragment="").read()
        )
        self.assertEqual(built_file, cmd.get_xml_file(built_file))

    def test_xml_reduce_generate_stats(self):
        stats_filename = generate_stats_file("/folder/test.xml", {})
        self.assertEqual(stats_filename, "stats-test.xml.json")

        stats_filename = generate_stats_file("test.xml", {})
        self.assertEqual(stats_filename, "stats-test.xml.json")
