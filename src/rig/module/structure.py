from typing import NamedTuple

from maya import cmds

from src.lib import attributes
from src.lib.nodes import Node

ModuleStructure = NamedTuple(
    "ModuleStructure", [
        ("module", Node),
        ("guides", Node),
        ("input", Node),
        ("logic", Node),
        ("controls", Node),
        ("deform", Node),
        ("output", Node)
    ])


def build_module_structure(module_name: str, parent: Node | None = None) -> ModuleStructure:
    """
    Build module structure.
    :param module_name: Module name
    :param parent: Parent node
    :return: None
    """
    struct = ModuleStructure(
        Node(cmds.createNode("transform", name=f"{module_name}_module")),
        Node(cmds.createNode("transform", name=f"{module_name}_guides", parent=f"{module_name}_module")),
        Node(cmds.createNode("transform", name=f"{module_name}_input", parent=f"{module_name}_module")),
        Node(cmds.createNode("transform", name=f"{module_name}_logic", parent=f"{module_name}_module")),
        Node(cmds.createNode("transform", name=f"{module_name}_controls", parent=f"{module_name}_module")),
        Node(cmds.createNode("transform", name=f"{module_name}_deform", parent=f"{module_name}_module")),
        Node(cmds.createNode("transform", name=f"{module_name}_output", parent=f"{module_name}_module")),
    )

    for group in struct:
        for attr in attributes.TRANSFORM_ATTRS:
            attributes.lock_and_hide_attr(str(group), attr)
            group.inheritsTransform.value = False

    if parent:
        cmds.parent(str(struct.module), str(parent))

    return struct

