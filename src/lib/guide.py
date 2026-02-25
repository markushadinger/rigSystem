from maya import cmds

from src.lib import naming, tags

GUIDE_TAG = "guide"
GUIDE_SUFFIX = "guide"


def get_name(node: str) -> str:
    return f"{node}_guide"


def get_all_component_guides(component: str) -> set[str]:
    """
    get all guides for a given component
    :param component:
    :return:
    """
    return {n for n in tags.find_all_with_tag(GUIDE_TAG) if tags.get_component_tag(n) == component}


def create_guide_joint(name: str, component: str) -> str:
    """
    Create a guide joint.
    :param name: Name of the joint
    :param component: Component name
    :return: Name of the joint
    """
    jnt = cmds.createNode("joint", name=name)
    tags.add_tag(jnt, GUIDE_TAG)
    tags.add_component_tag(jnt, component)
    return jnt


def get_guide_data(node: str) -> list[float]:
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
