from maya import cmds
from maya.api import OpenMaya

from src.lib import tags
from src.lib import naming
from src.lib.nodes import Node, Plug
from src.rig.controls import shape

CONTROL_TAG = "control"
SUFFIX = "ctrl"

PARENT_MLT_INDEX = 10
OFFSET_MLT_INDEX = 9


def build(name: naming.Name) -> Node:
    control = Node.create("transform", name=str(name.replace(suffix=SUFFIX)))
    tags.add_tag(control, CONTROL_TAG)
    tags.add_component_tag(control, name.component_name)
    # cmds.controller(control)
    return control


def add_shape(control: Node, shape_node: Node):
    shape.assign_shape_to_transform(control, shape_node)


def add_shape_from_dict(control: Node, shape_data: dict):
    shape_node = shape.create(**shape_data)
    shape.assign_shape_to_transform(shape_node, control)


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


def get_all_component_controls(component: str) -> set[Node]:
    """
    Get all controls for a given component.
    :param component: Component name
    :return: Set of control names
    """
    return {Node(n) for n in tags.find_all_with_tag(CONTROL_TAG) if tags.get_component_tag(n) == component}
