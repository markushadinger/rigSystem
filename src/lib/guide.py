from maya import cmds

from src.lib import tags

GUIDE_TAG = "guide"
COMPONENT_ATTR = "component"


def get_name(node: str) -> str:
    return f"{node}_guide"


def add_module_tag(node: str, component: str) -> None:
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

def get_all_component_guides(component: str) -> set[str]:
    """
    get all guides for a given component
    :param component:
    :return:
    """
    return {n for n in tags.find_all_with_tag(GUIDE_TAG) if get_component_tag(n) == component}


def create_guide_joint(name: str, component: str) -> str:
    """
    Create a guide joint.
    :param name: Name of the joint
    :param component: Component name
    :return: Name of the joint
    """
    jnt = cmds.createNode("joint", name=name)
    tags.add_tag(jnt, GUIDE_TAG)
    add_module_tag(jnt, component)
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
    return {guide: get_guide_data(guide) for guide in guides}
