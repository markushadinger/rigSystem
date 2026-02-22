from maya import cmds

TRANSLATE_ATTRS = ("translateX", "translateY", "translateZ")
ROTATE_ATTRS = ("rotateX", "rotateY", "rotateZ")
SCALE_ATTRS = ("scaleX", "scaleY", "scaleZ")
TRANSFORM_ATTRS = TRANSLATE_ATTRS + ROTATE_ATTRS + SCALE_ATTRS
VISIBILITY_ATTR = "visibility"
UNIFORM_SCALE_ATTR = "uniformScale"


def lock_and_hide_attr(node: str, attr: str | list[str]) -> None:
    """
    Lock and hide an attribute.
    :param node: Node to lock and hide attribute on
    :param attr: Attribute to lock and hide
    :return: None
    """
    if isinstance(attr, str):
        attr = [attr]

    for a in attr:
        cmds.setAttr(f"{node}.{a}", lock=True, keyable=False, channelBox=False)


def make_unkeyable(node: str, attr: str | list[str]) -> None:
    """
    Make an attribute unkeyable.
    :param node: Node to make attribute unkeyable on
    :param attr: Attribute to make unkeyable
    :return: None
    """
    if isinstance(attr, str):
        attr = [attr]

    for a in attr:
        cmds.setAttr(f"{node}.{a}", keyable=False, channelBox=True)


def convert_to_uniform_scale(node: str) -> None:
    """
    Convert a node to use uniform scale.
    :param node: Node to convert to uniform scale
    :return: None
    """
    cmds.aliasAttr(UNIFORM_SCALE_ATTR, f"{node}.scaleY")
    cmds.connectAttr(f"{node}.{UNIFORM_SCALE_ATTR}", f"{node}.scaleX")
    cmds.connectAttr(f"{node}.{UNIFORM_SCALE_ATTR}", f"{node}.scaleZ")
    lock_and_hide_attr(node, "scaleX")
    lock_and_hide_attr(node, "scaleZ")
