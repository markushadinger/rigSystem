from maya import cmds

from src.rig.controls import control, shape, color
from src.lib.nodes import Plug, Node


def build_fk_controls(
        names: list[str],
        matrices: list,
        parent_mtx_plug: Plug,
        parent_node: Node
) -> list[Node]:
    """
    Build FK controls.
    :param names: names of the controls
    :param matrices: matrices of the controls
    :param parent_mtx_plug: input plug of the parent matrix to connect to the first control
    :param parent_node: parent node to parent the controls under
    :return:
    """

    nodes = []
    parent_ctrl: None | Node = None

    for name, matrix in zip(names, matrices):
        ctrl = control.build(name)
        shape.set_shape(ctrl, shape.scale_shape(shape.CIRCLE, 20))
        color.set_color(ctrl, color.COLOR_YELLOW)

        cmds.parent(ctrl, parent_node)
        ctrl.inOffsetMatrix.value = matrix

        if parent_ctrl:
            control.set_parent_control(ctrl, parent_ctrl)
        elif parent_mtx_plug:
            ctrl.inParentMatrix.connect(parent_mtx_plug)

        parent_ctrl = ctrl
        nodes.append(ctrl)

    return nodes
