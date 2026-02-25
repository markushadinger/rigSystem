import json

from maya import cmds

TAG_ATTR = "tags"
COMPONENT_ATTR = "component"


def add_tag_attr(node: str) -> None:
    """
    Add a tag attribute to a node if it doesn't exist.
    :param node: Node to add tag attribute to
    :return:
    """
    if not cmds.objExists(f"{node}.{TAG_ATTR}"):
        cmds.addAttr(node, ln=TAG_ATTR, dt="string")


def get_tags(node: str) -> list[str]:
    """
    Get tags for a node
    :param node: Node to get tags for
    :return: List of tags
    """
    add_tag_attr(node)
    return json.loads(cmds.getAttr(f"{node}.{TAG_ATTR}") or "[]")


def set_tags(node: str, tags: list[str]) -> None:
    """
    Set tags for a node
    :param node: Node to set tags for
    :param tags: List of tags
    :return: None
    """
    add_tag_attr(node)
    cmds.setAttr(f"{node}.{TAG_ATTR}", json.dumps(tags), type="string")


def add_tag(node: str, tag: str) -> None:
    """
    Add a tag to a node
    :param node: Node to add tag to
    :param tag: Tag to add
    :return: None
    """
    add_tag_attr(node)
    current_tags = get_tags(node)

    if tag not in current_tags:
        current_tags.append(tag)
        set_tags(node, current_tags)


def remove_tag(node: str, tag: str) -> None:
    """
    Remove a tag from a node
    :param node: Node to remove tag from
    :param tag: Tag to remove
    :return: None
    """
    add_tag_attr(node)
    current_tags = get_tags(node)
    if tag in current_tags:
        current_tags.remove(tag)
        set_tags(node, current_tags)


def has_tag(node: str, tag: str) -> bool:
    """
    Check if a node has a specific tag.
    :param node:
    :param tag:
    :return:
    """
    return tag in get_tags(node)


def find_all_with_tag(tag: str) -> list[str]:
    """
    Find all nodes with a specific tag.
    :param tag:
    :return:
    """
    nodes_with_tag = [n.split(".")[0] for n in cmds.ls(f"*.{TAG_ATTR}")]
    return [node for node in nodes_with_tag if has_tag(node, tag)]


def add_component_tag(node: str, component: str) -> None:
    """
    Add a module tag to a node.
    :param node: Node to add module tag to
    :param component: Component name
    :return: None
    """
    cmds.addAttr(node, longName=COMPONENT_ATTR, dataType="string")
    cmds.setAttr(f"{node}.{COMPONENT_ATTR}", component, type="string", lock=True)


def get_component_tag(node: str) -> str:
    """
    Get a component tag from a node.
    :param node: Node to get component tag from
    :return: Component tag or None
    """
    if not cmds.objExists(f"{node}.{COMPONENT_ATTR}"):
        print(f"Node {node}.{COMPONENT_ATTR} does not have a component tag.")
        return ""

    return cmds.getAttr(f"{node}.{COMPONENT_ATTR}")
