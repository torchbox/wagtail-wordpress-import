import shortcodes


def find_all_shortcodes(text):
    found_shortcodes = []

    if "[" in text:
        lexer = shortcodes.Lexer(text, "[", "]", "\\[")
        try:
            for token in lexer.tokenize():
                if token.type == "TAG":
                    shortcode_name = token.text.split(" ")[0]

                    # Ignore closing shortcodes
                    if not shortcode_name.startswith("/"):
                        found_shortcodes.append(shortcode_name)
        except shortcodes.ShortcodeSyntaxError:
            return []

    return found_shortcodes
