from dataclasses import replace

from maya import cmds

from src.lib import tags
from src.lib.nodes import Node
from src.lib import naming

SKIN_TAG = "skin"
SKIN_SUFFIX = "skn"
JNT_SUFFIX = "jnt"


def create(name: naming.Name | str, skin_joint=True) -> Node:
    """
    Create a joint with the given name and component tag.
    :param name: Name of the joint
    :param skin_joint: Whether to add a skin tag to the joint
    :return: The created joint node
    """
    jnt = Node.create("joint", str(name))
    tags.add_component_tag(jnt, name.component_name)
    if skin_joint:
        tags.add_tag(jnt, SKIN_TAG)
    return jnt


def create_chain(matrices: list, name: naming.Name, skin_joint=True) -> list[Node]:
    ret = []
    for i, m in enumerate(matrices):
        jnt = create(replace(name, index=i), skin_joint)
        cmds.xform(jnt, worldSpace=True, matrix=m)
        ret.append(jnt)

    return ret
