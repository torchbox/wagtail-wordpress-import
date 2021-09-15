from django.test import TestCase
from wagtail_xmlimport.management.commands import runxml
from wagtail_xmlimport.management.commands.runxml import Command as RunCmd
from wagtail_xmlimport.management.commands.reduce import Command as ReduceCmd
from wagtail_xmlimport.management.commands.discovery import Command as DiscoveryCmd


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
