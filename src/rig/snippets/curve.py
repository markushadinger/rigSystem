from maya import cmds

from src.lib.nodes import Node, Plug
from src.rig.controls import shape


def build_matrix_driven_curve(name: str, matrix_plugs: [Plug], degree: int = 3) -> Node:
    """
    Build a curve driven by the given matrix plugs.
    :param name: name of the curve
    :param matrix_plugs: list of plugs to connect to the control points of the curve
    :param degree: the degree of the curve, default is 3 (cubic)
    :return:
    """

    curve_node = Node(cmds.curve(p=[(0, 0, 0)] * len(matrix_plugs), degree=degree, name=name))
    shape_node = shape.get_shape_node(curve_node)

    for i, matrix_plug in enumerate(matrix_plugs):
        shape_node.controlPoints[i].connect(matrix_plug)

    return curve_node
