from maya import cmds
from src.lib.nodes import Node, Plug
from src.rig.controls import shape


def generate_placeholder_knots(u_count: int, v_count: int) -> list:
    ret = []
    for u in range(u_count):
        for v in range(v_count):
            ret.append((float(v), float(u), 0.0))

    return ret


def get_k(degree: int, knot_count: int) -> list[int]:
    k_len = knot_count + degree - 1

    k_0 = 0
    k_n = k_len - 2 * degree + 1

    k_start = [k_0] * degree
    k_end = [k_n] * degree
    k_mid = list(range(k_0 + 1, k_n))

    return k_start + k_mid + k_end


def create_matrix_driven_surface(name: str, matrices: list[Plug], degree: int = 3) -> Node:
    """
    Creates a surface driven by the given matrices.
    :param name: The name of the surface.
    :param matrices: A list of plugs that output matrices to drive the surface.
    :param degree: The degree of the surface.
    :return: The Node of the created surface.
    """

    driver_plugs = []

    for mtx in matrices:
        trl = Node.create("translationFromMatrix", name=f"{name}_{mtx.node}_tf")
        trl.input.connect(mtx)

        axis = Node.create("axisFromMatrix", name=f"{name}_{mtx.node}_aim")
        axis.input.connect(mtx)

        pos_left = Node.create("plusMinusAverage", "test")
        pos_left.input3D[0].connect(trl.output)
        pos_left.input3D[1].connect(axis.output)
        pos_left.operation.value = 1

        pos_right = Node.create("plusMinusAverage", "test")
        pos_right.input3D[0].connect(trl.output)
        pos_right.input3D[1].connect(axis.output)
        pos_right.operation.value = 2

        driver_plugs.append((pos_left.output3D, pos_right.output3D))

    ku = get_k(degree, len(matrices))
    shape_node = cmds.surface(du=degree, dv=1, ku=ku, kv=(0, 1), p=generate_placeholder_knots(len(matrices), 2))
    shape_node = Node(shape_node)

    for i, (l_plug, r_plug) in enumerate(driver_plugs):
        shape_node.controlPoints[i * 2].connect(l_plug)
        shape_node.controlPoints[i * 2 + 1].connect(r_plug)
