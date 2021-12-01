from unittest.mock import patch
from django.test import TestCase, override_settings
from django.core.management import call_command, CommandError
from wagtail_wordpress_import.management.commands.import_xml import Command as RunCmd
from wagtail_wordpress_import.management.commands.reduce_xml import Command as ReduceCmd
from wagtail_wordpress_import.xml_boilerplate import (
    build_xml_stream,
    generate_temporay_file,
)


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
        built_file = generate_temporay_file(
            build_xml_stream(xml_tags_fragment="").read()
        )

        with self.assertRaises(FileNotFoundError):
            # In testing there is no log folder
            # the command should raise this as an error
            call_command(
                "import_xml", built_file, "2", "-a", "example", "-m", "TestPage"
            )


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
            xml_file = cmd.get_xml_file("test.xml")
        with self.assertRaises(SystemExit):
            xml_file = cmd.get_xml_file("folder/test.xml")

        built_file = generate_temporay_file(
            build_xml_stream(xml_tags_fragment="").read()
        )
        self.assertEqual(built_file, cmd.get_xml_file(built_file))
