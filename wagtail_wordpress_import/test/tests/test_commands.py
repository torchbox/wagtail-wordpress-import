from django.test import TestCase
from wagtail_wordpress_import.management.commands import import_xml
from wagtail_wordpress_import.management.commands.import_xml import Command as RunCmd
from wagtail_wordpress_import.management.commands.reduce_xml import Command as ReduceCmd
from wagtail_wordpress_import.management.commands.extract_xml_mapping import Command as DiscoveryCmd


class TestRunXmlCommand(TestCase):
    def setUp(self):
        self.cmd = RunCmd()

    def test_command(self):
        self.assertIsInstance(self.cmd, RunCmd)


class TestReduceCommand(TestCase):
    def setUp(self):
        self.cmd = ReduceCmd()

    def test_command(self):
        self.assertIsInstance(self.cmd, ReduceCmd)


class TestDiscoverCommands(TestCase):
    def setUp(self):
        self.cmd = DiscoveryCmd()

    def test_command(self):
        self.assertIsInstance(self.cmd, DiscoveryCmd)
