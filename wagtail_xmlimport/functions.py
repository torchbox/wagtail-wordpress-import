from collections import defaultdict


def clean_node_name(node_name):
    return node_name.replace("-", "_")


def coerce_node_value(value):
    if value.isnumeric():
        return int(value)
    if value == "true":
        return True
    if value == "false":
        return False
    return value


def get_node_value(node):
    if len(node.childNodes) == 0:
        return node.nodeName, None
    else:
        contains_element_node = False
        for child_node in node.childNodes:
            if child_node.nodeType == node.ELEMENT_NODE:
                contains_element_node = True
                break
        if contains_element_node:
            return node.nodeName, node_to_dict(node)
        else:
            return node.nodeName, coerce_node_value(
                "".join(child_node.nodeValue for child_node in node.childNodes)
            )


def node_to_dict(node):
    obj = defaultdict(list)
    for child_node in node.childNodes:
        if child_node.nodeType == node.ELEMENT_NODE:
            name, value = get_node_value(child_node)
            obj[clean_node_name(name)].append(value)
        elif child_node.nodeType == node.TEXT_NODE:
            pass  # Usually whitespace
        else:
            raise Exception()
    # If an element appears more than once, use an array.
    # Otherwise just use the element value.
    obj = {key: value[0] if len(value) == 1 else value for key, value in obj.items()}
    if obj == {"nil": True}:
        return None
    return obj


# doc = pulldom.parse('millennialmoney.WordPress.2021-07-28.xml')
# for event, node in doc:
#     if event == pulldom.START_ELEMENT and node.tagName == 'item':
#         doc.expandNode(node)
#         dict = node_to_dict(node)
#         print(dict['wp:post_type'], dict['wp:status'])
#         if dict['wp:post_type'] == 'newsarticles':
#             import pdb; pdb.set_trace()
