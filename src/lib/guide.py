from maya import cmds
from maya.api import OpenMaya

from src.lib import naming, tags
from src.lib.nodes import Node

GUIDE_TAG = "guide"
SUFFIX = "guide"

DEFAULT_VALUE = [
    1, 0, 0, 0,
    0, 1, 0, 0,
    0, 0, 1, 0,
    0, 0, 0, 1
]


def get_name(node: str) -> str:
    return f"{node}_guide"


def get_all_component_guides(component: str) -> set[str]:
    """
    get all guides for a given component
    :param component:
    :return:
    """
    return {n for n in tags.find_all_with_tag(GUIDE_TAG) if tags.get_component_tag(n) == component}


def create_guide_joint(name: str | naming.Name) -> str:
    """
    Create a guide joint.
    :param name: Name of the joint
    :param component: Component name
    :return: Name of the joint
    """
    jnt = Node.create("joint", name=name.replace(suffix=SUFFIX))
    tags.add_tag(jnt, GUIDE_TAG)
    tags.add_component_tag(jnt, name.component_name)
    return jnt


def get_guide_data(node: str | Node) -> list[float]:
    """
    Get guide data for a given node.
    :param node: Node to get guide data for
    :return: List of guide data
    """
    return cmds.xform(node, query=True, worldSpace=True, matrix=True)


def get_guide_data_for_component(component: str) -> dict[str, any]:
    """
    Get guide data for a given component.
    :param component: Component name
    :return: Dictionary of guide data
    """
    guides = get_all_component_guides(component)
    return {naming.strip_suffix(guide): get_guide_data(guide) for guide in guides}


def get_guide_node(name: naming.Name) -> Node:
    """
    Returns a guide node based on the name
    :param name:
    :return:
    """
    return Node(str(name.replace(suffix=GUIDE_TAG, extra=None)))


def get_world_matrix(name: naming.Name) -> OpenMaya.MMatrix:
    """
    Return the worldMatrix of a node
    :param name:
    :return:
    """

    guide_node = get_guide_node(name)

    if not guide_node.exists():
        return OpenMaya.MMatrix(DEFAULT_VALUE)

    return OpenMaya.MMatrix(get_guide_node(name).worldMatrix[0].value)
