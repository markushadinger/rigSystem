from maya.api.OpenMaya import MVector, MPoint, MMatrix, MEulerRotation

from src.lib.nodes import Node, Plug
from maya import cmds


def get_matrix(node: Node, world_space: bool = True) -> MMatrix:
    return MMatrix(cmds.xform(node, query=True, worldSpace=world_space, matrix=True))


def set_matrix(node, matrix: MMatrix, world_space: bool = True):
    cmds.xform(node, worldSpace=world_space, matrix=matrix)


def get_position(node: Node, world_space: bool = True) -> MPoint:
    return MPoint(cmds.xform(node, query=True, translation=True, worldSpace=world_space))


def set_position(node, position: MPoint | MVector | list, world_space: bool = True):
    cmds.xform(node, worldSpace=world_space, translation=list(position)[:3])


def get_scale(node: Node, world_space: bool = True) -> MVector:
    return MVector(cmds.xform(node, query=True, scale=True, worldSpace=world_space))


def set_scale(node, scale: MVector | list, world_space: bool = True):
    cmds.xform(node, worldSpace=world_space, scale=list(scale))


def get_rotation(node: Node, world_space: bool = True) -> MEulerRotation:
    return MEulerRotation(cmds.xform(node, query=True, worldSpace=world_space, rotation=True))


def set_rotation(node: Node, rotation: MEulerRotation, world_space=True):
    cmds.xform(node, worldSpace=world_space, rotation=list(rotation))


def reset_rotation(node: Node, world_space: bool = True):
    cmds.xform(node, worldSpace=world_space, rotation=[0, 0, 0])


def match(target: Node, source: Node):
    set_matrix(target, get_matrix(source))


def freeze(node: Node, apply: bool = False):
    cmds.makeIdentity(node, apply=apply)


def get_vector(node: Node, axis: str, world_space: bool = True) -> MVector:
    row = "xyz".index(axis.lower())
    mtx = get_matrix(node, world_space)

    return MVector([
        mtx.getElement(row * 4 + 0),
        mtx.getElement(row * 4 + 1),
        mtx.getElement(row * 4 + 2),
    ])


def matrix_constraint(node: Node, mtx_plug: Plug, offset: bool = True):
    mtx = get_matrix(node)
    node.offsetParentMatrix.connect(mtx_plug)
    node.inheritsTransform.value = False

    if offset:
        set_matrix(node, mtx)
