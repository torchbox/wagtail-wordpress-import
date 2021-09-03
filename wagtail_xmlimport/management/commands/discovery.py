from django.core.management.base import BaseCommand
from lxml import etree

class Command(BaseCommand):
    def __init__(self, xml):
        self.tree = etree.ElementTree(etree.fromstring(xml))