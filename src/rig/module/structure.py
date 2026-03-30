from typing import NamedTuple

from maya import cmds

from src.lib import attributes, naming
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


def build_module_structure(name: naming.Name, parent: Node | None = None) -> ModuleStructure:
    """
    Build module structure.
    :param name: Module name
    :param parent: Parent node
    :return: None
    """

    name = str(name)
    struct = ModuleStructure(
        Node.create("transform", name=name),
        Node.create("transform", name=f"{name}_guides", parent=name),
        Node.create("transform", name=f"{name}_input", parent=name),
        Node.create("transform", name=f"{name}_logic", parent=name),
        Node.create("transform", name=f"{name}_controls", parent=name),
        Node.create("transform", name=f"{name}_deform", parent=name),
        Node.create("transform", name=f"{name}_output", parent=name),
    )

    for group in struct:
        for attr in attributes.TRANSFORM_ATTRS:
            attributes.lock_and_hide_attr(str(group), attr)
            group.inheritsTransform.value = False

    if parent:
        cmds.parent(str(struct.module), str(parent))

    return struct
