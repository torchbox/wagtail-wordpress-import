import tempfile
from io import StringIO

xml_stream_header = StringIO(
    """
    <rss xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/" xmlns:wp="http://wordpress.org/export/1.2/" version="2.0">
    <channel>
        <title>Foo</title>
        <link>https://www.example.com</link>
        <pubDate>Fri, 30 Jul 2021 11:56:01 +0000</pubDate>
        <language>en-US</language>
        <wp:wxr_version>1.2</wp:wxr_version>
        <wp:base_site_url>https://www.budgetsaresexy.com</wp:base_site_url>
        <wp:base_blog_url>https://www.budgetsaresexy.com</wp:base_blog_url>"""
).read()

xml_stream_footer = StringIO(
    """
    </channel>
    </rss>
    """
).read()


def build_xml_stream(xml_tags_fragment="", xml_items_fragment=""):
    """Formats the boilerplate XML template with the provided fragment for top level tags."""

    return StringIO(
        xml_stream_header + xml_tags_fragment + xml_items_fragment + xml_stream_footer
    )


def generate_temporary_file(xml_stream):

    temp_file = tempfile.NamedTemporaryFile(delete=False)

    with open(temp_file.name, "w") as f:
        f.write(xml_stream)

    return temp_file.name
