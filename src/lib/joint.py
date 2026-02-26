from src.lib import tags
from src.lib.nodes import Node

from maya import cmds

SKIN_TAG = "skin"
SKIN_SUFFIX = "skn"
JNT_SUFFIX = "jnt"


def create(name: str, component_name: str, skin_joint=True) -> Node:
    """
    Create a joint with the given name and component tag.
    :param name: Name of the joint
    :param component_name: Name of the component to tag the joint with
    :param skin_joint: Whether to add a skin tag to the joint
    :return: The created joint node
    """
    jnt = Node.create("joint", name)
    tags.add_component_tag(jnt, component_name)
    if skin_joint:
        tags.add_tag(jnt, SKIN_TAG)
    return jnt
