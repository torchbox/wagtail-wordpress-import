from typing import Pattern
import re


class BlockShortcodeHandler:

    @property
    def _pattern(self) -> Pattern:
        """Return a regex to match a block shortcode and capture the attrs and text.

        Given an input:

            "Preface [foo bar=1]some text[/foo] epilogue."

        the regex will match the string between the two "foo" tags, inclusively. The
        capture group "attrs" will match " bar=1", and capture group "content" will
        match "some text".
        """
        if not hasattr(self, "tag_name"):
            raise NotImplementedError(
                "Create a subclass of BlockShortcodeHandler with a tag_name attribute"
            )

        return re.compile(
            r"\["  # matches the opening [
            + self.tag_name
            + r"\b"  # matches a word boundary
            + r"(?P<attrs>[^\]]*)"  # capture 'attrs', matching anything but ]
            + r"\]"  # matches the closing ] of the opening tag
            + r"(?P<content>.*?)"  # non-greedily captures 'content' between the tags
            + r"\[\/"  # matches the  [/ of the closing tag
            + self.tag_name
            + r"\]"  # matches the closing ]
        )

    def pre_filter(self, string: str) -> str:
        """Replace all occurrences of the tag with a HTML tag for later parsing.

        Given an input:

            "Preface [foo bar=1]some text[/foo] epilogue."

        this function will return

            "Preface <wagtail_block_foo bar=1>some text</wagtail_block_foo> epilogue."
        """
        string, matches = self._pattern.subn(
            r"<"
            + self.element_name
            + r"\g<attrs>>\g<content></"
            + self.element_name
            + r">",
            string,
        )

        return string

    @property
    def element_name(self) -> str:
        return f"wagtail_block_{self.tag_name}"

# Subclasses should declare a tag_name, and provide a construct_block method for
# converting their prefiltered HTML to Wagtail StreamField block JSON.
class CaptionHandler:

    tag_name = "caption"

    def construct_block(self):
        pass
