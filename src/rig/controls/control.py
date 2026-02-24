from maya import cmds
from maya.api import OpenMaya

from src.lib import tags
from src.lib.nodes import Node, Plug

CONTROL_TAG = "control"
SUFFIX = "ctrl"

PARENT_MLT_INDEX = 10
OFFSET_MLT_INDEX = 9


def get_name(name: str, index: str | None = None, side: str | None = None) -> str:
    return "_".join(filter(None, [name, index, side, "ctrl"]))


def build(name: str) -> Node:
    control = Node.create("transform", name=name)
    tags.add_tag(control, CONTROL_TAG)
    build_offset_network(control)
    return control


def add_shape(control: str, shape: str) -> None:
    cmds.parent(shape, control)


def load_shape(control: str, shape_path: str) -> None:
    shape = cmds.file(shape_path, i=True, returnNewNodes=True)[0]
    add_shape(control, shape)


def build_offset_network(control: Node):
    cmds.addAttr(control, longName="inParentMatrix", attributeType="matrix")
    cmds.addAttr(control, longName="inOffsetMatrix", attributeType="matrix")

    mlt = Node.create("multMatrix", name=f"{control}_hierarchy_mlt")
    mlt.matrixIn[PARENT_MLT_INDEX].connect(control.inParentMatrix)
    mlt.matrixIn[OFFSET_MLT_INDEX].connect(control.inOffsetMatrix)
    control.offsetParentMatrix.connect(mlt.matrixSum)


def get_normalized_matrix_output(control: Node) -> Plug:
    mlt = Node.create("multMatrix", name=f"{control}_normalized_mlt")
    mlt.matrixIn[0].value = control.worldInverseMatrix[0].value
    mlt.matrixIn[1].connect(control.worldMatrix[0])
    return mlt.matrixSum


def set_parent_control(child: Node, parent: Node) -> None:
    """
    Set the parent control for a child control. This will maintain the child's current world transform.
    :param child: Child control to set parent for
    :param parent: Parent control to set
    :return: None
    """
    child_matrix = OpenMaya.MMatrix(child.worldMatrix[0].value)
    parent_matrix = OpenMaya.MMatrix(parent.worldMatrix[0].value)
    offset_matrix = child_matrix * parent_matrix.inverse()

    child.inParentMatrix.connect(parent.worldMatrix[0])
    child.inOffsetMatrix.value = offset_matrix
