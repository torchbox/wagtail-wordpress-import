from collections import Counter

from django.test.html import HTMLParseError, parse_html

from .shortcodes import find_all_shortcodes


class HTMLAnalyzer:
    def __init__(self):
        self.total = 0
        self.invalid = 0
        self.tags_total = Counter()
        self.attributes_total = Counter()
        self.styles_total = Counter()
        self.classes_total = Counter()
        self.shortcodes_total = Counter()

        self.tags_unique_pages = Counter()
        self.attributes_unique_pages = Counter()
        self.styles_unique_pages = Counter()
        self.classes_unique_pages = Counter()
        self.shortcodes_unique_pages = Counter()

    @classmethod
    def find_all_tags(cls, dom):
        names = Counter()
        for child in dom.children:
            if isinstance(child, str):
                continue

            names[child.name[:30]] += 1
            names.update(cls.find_all_tags(child))

        return names

    @classmethod
    def find_all_attributes(cls, dom):
        attrs = Counter()
        for child in dom.children:
            if isinstance(child, str):
                continue

            for attr_name, attr_value in child.attributes:
                attrs[(child.name[:30], attr_name[:30])] += 1

            attrs.update(cls.find_all_attributes(child))

        return attrs

    @classmethod
    def find_all_styles(cls, dom):
        styles = Counter()
        for child in dom.children:
            if isinstance(child, str):
                continue

            for attr_name, attr_value in child.attributes:
                if attr_name == "style":
                    for rule in attr_value.split(";"):
                        if rule.strip():
                            styles[(child.name[:30], rule.strip()[:30])] += 1

            styles.update(cls.find_all_styles(child))

        return styles

    @classmethod
    def find_all_classes(cls, dom):
        classes = Counter()
        for child in dom.children:
            if isinstance(child, str):
                continue

            for attr_name, attr_value in child.attributes:
                if attr_name == "class":
                    for class_name in attr_value.split(" "):
                        classes[(child.name[:30], class_name.strip()[:30])] += 1

            classes.update(cls.find_all_classes(child))

        return classes

    @classmethod
    def find_all_shortcodes(cls, dom):
        shortcodes = Counter()
        for child in dom.children:
            if isinstance(child, str):
                shortcodes.update(find_all_shortcodes(child))
            else:
                shortcodes.update(cls.find_all_shortcodes(child))

        return shortcodes

    def analyze(self, html):
        self.total += 1

        try:
            dom = parse_html(html)
        except HTMLParseError:
            self.invalid += 1
            return

        tags = self.find_all_tags(dom)
        attributes = self.find_all_attributes(dom)
        styles = self.find_all_styles(dom)
        classes = self.find_all_classes(dom)
        shortcodes = self.find_all_shortcodes(dom)

        self.tags_total.update(tags)
        self.attributes_total.update(attributes)
        self.styles_total.update(styles)
        self.classes_total.update(classes)
        self.shortcodes_total.update(shortcodes)

        self.tags_unique_pages.update(tags.keys())
        self.attributes_unique_pages.update(attributes.keys())
        self.styles_unique_pages.update(styles.keys())
        self.classes_unique_pages.update(classes.keys())
        self.shortcodes_unique_pages.update(shortcodes.keys())
