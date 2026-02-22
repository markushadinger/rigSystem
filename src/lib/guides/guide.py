from maya import cmds

from src.lib import tags

GUIDE_TAG = "guide"
MODULE_ATTR = "module"


def get_name(node: str) -> str:
    return f"{node}_guide"


def add_module_tag(node: str, module: str) -> None:
    """
    Add a module tag to a node.
    :param node: Node to add module tag to
    :param module: Module name
    :return: None
    """
    cmds.addAttr(node, longName=MODULE_ATTR, dataType="string")
    cmds.setAttr(f"{node}.{MODULE_ATTR}", module, type="string", lock=True)


def get_module_tag(node: str) -> str:
    """
    Get a module tag from a node.
    :param node: Node to get module tag from
    :return: Module tag or None
    """
    if not cmds.objExists(f"{node}.{MODULE_ATTR}"):
        return ""

    return cmds.getAttr(f"{node}.{MODULE_ATTR}")


def get_all_module_guides(module: str) -> set[str]:
    """
    get all guides for a given module
    :param module:
    :return:
    """
    return {n for n in cmds.ls(f"*.{MODULE_ATTR}") if get_module_tag(n) == module and tags.has_tag(n, GUIDE_TAG)}


def create_guide_joint(name: str, module: str) -> str:
    """
    Create a guide joint.
    :param name: Name of the joint
    :param module: Module name
    :return: Name of the joint
    """
    jnt = cmds.createNode("joint", name=name)
    tags.add_tag(jnt, GUIDE_TAG)
    add_module_tag(jnt, module)
    return jnt


def get_guide_data(node: str) -> list[float]:
    """
    Get guide data for a given node.
    :param node: Node to get guide data for
    :return: List of guide data
    """
    return cmds.xform(node, query=True, worldSpace=True, matrix=True)


def get_guide_data_for_module(module: str) -> dict[str, any]:
    """
    Get guide data for a given module.
    :param module: Module name
    :return: Dictionary of guide data
    """
    guides = get_all_module_guides(module)
    return {guide: get_guide_data(guide) for guide in guides}
