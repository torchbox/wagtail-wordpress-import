import re


class InlineShortcodeHandler:
    """Subclasses should declare a shortcode_name and provide
    a construct_html_tag method for converting the shortcode to a HTML tag.
    """

    inline_shortcode_name: str

    element_name = "span"

    def __init__(self):
        # Subclasses should declare a shortcode_name
        if not hasattr(self, "shortcode_name"):
            raise NotImplementedError(
                "Create a subclass of BlockShortcodeHandler with a shortcode_name attribute"
            )
        pattern = re.compile(r"^\S[a-zA-Z0-9_\S]+\S$")
        # shortcode_name must use upper or lower case letters or digits and cannot contain spaces
        if not pattern.match(self.shortcode_name):
            raise ValueError(
                "The shortcode_name attribute must use upper or lower case letters or digits and cannot contain spaces"
            )

    @property
    def _pattern(self):
        """Return a regex to match an inline shortcode and capture the attrs.

        Given an input:

            "Preface [foo bar=1] epilogue."

        the regex will match the string between the "[" and "]"  tags. The
        capture group "attrs" will match " bar=1", and capture group "shortcodename" will
        match "foo".
        \[(\S+)(?:\s)(\w\S.+)\]
        """  # noqa: W605

        return re.compile(
            r"\["  # matches the opening [
            + self.shortcode_name
            + r"(?:\s)"  # matches a single space
            + r"(?P<attrs>[^\]]*)"  # capture 'attrs', matching anything but ]
            + r"\]"  # matches the closing ] of the opening tag
        )

    @staticmethod
    def get_shortcode_attrs(string):
        """Create and return a dict of the attrs of a shortcode."""
        attrs = string.split(" ")
        attrs = [attr.split("=") for attr in attrs]
        return {attr[0]: attr[1].replace('"', "") for attr in attrs}
