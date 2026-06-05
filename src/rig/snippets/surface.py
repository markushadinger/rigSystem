from maya import cmds

from src.lib.nodes import Node, Plug
from maya.api import OpenMaya


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


class MatrixRibbonBuilder:
    """
    Build a ribbon surface driven by a list of matrix plugs.
    Each matrix plug will drive two control points on the surface,
    one on the left and one on the right.
    """

    def __init__(self):
        # settings
        self.surface_name: str = "matrix_ribbon_surf"
        self.degree: int = 3

        # inputs
        self.in_matrix_plugs: list[Plug] = []

        # outputs
        self.out_surface_shape: Node | None = None
        self.out_surface_transform: Node | None = None
        self.flip_indices: list[int] = []

    def build(self):
        driver_plugs = []
        for i, mtx in enumerate(self.in_matrix_plugs):
            trl = Node.create("translationFromMatrix", name=f"{self.surface_name}_{mtx.node}_tf")
            trl.input.connect(mtx)

            axis = Node.create("axisFromMatrix", name=f"{self.surface_name}_{mtx.node}_aim")
            axis.input.connect(mtx)

            pos_left = Node.create("plusMinusAverage", "test")
            pos_left.input3D[0].connect(trl.output)
            pos_left.input3D[1].connect(axis.output)
            pos_left.operation.value = 2 if i in self.flip_indices else 1

            pos_right = Node.create("plusMinusAverage", "test")
            pos_right.input3D[0].connect(trl.output)
            pos_right.input3D[1].connect(axis.output)
            pos_right.operation.value = 1 if i in self.flip_indices else 2

            driver_plugs.append((pos_left.output3D, pos_right.output3D))

        self.out_surface_transform, self.out_surface_shape = build_nurbs_surface(
            name=self.surface_name,
            knot_u_count=len(self.in_matrix_plugs),
            degree=self.degree
        )
        self.out_surface_transform = Node(cmds.listRelatives(self.out_surface_shape, parent=True)[0])

        for i, (l_plug, r_plug) in enumerate(driver_plugs):
            self.out_surface_shape.controlPoints[i * 2].connect(l_plug)
            self.out_surface_shape.controlPoints[i * 2 + 1].connect(r_plug)


def get_points(matrices: list, width: float, flip_indices: list[int]) -> list[OpenMaya.MPoint]:
    """
    Return the points of the nurbs surface
    :param matrices:
    :param width:
    :param flip_indices:
    :return:
    """
    points = []

    for i, mtx in enumerate(matrices):
        center = OpenMaya.MPoint(mtx[12:15])
        side_vector = OpenMaya.MVector(mtx[0:3]) * (-1 if i in flip_indices else 1) * width
        points.append(center + side_vector)
        points.append(center - side_vector)

    return points


def build_nurbs_surface(name, knot_u_count: int, degree: int) -> tuple[Node, Node]:
    """
    build a nurbs surface based on the points and the degree
    :param name:
    :param knot_u_count:
    :param degree:
    :return:
    """

    ku = get_k(degree, knot_u_count)
    shape = Node.generate(
        cmds.surface,
        name=name,
        du=degree,
        dv=1,
        ku=ku,
        kv=(0, 1),
        p=generate_placeholder_knots(knot_u_count, 2)
    )
    transform = Node(cmds.listRelatives(shape, parent=True)[0])
    shape_node = cmds.rename(str(shape), f"{name}Shape")
    shape = Node(shape_node)

    return transform, shape


def set_points_on_surface(shape: Node, points: list[OpenMaya.MPoint]):
    """
    Assign points to a nurbs surface
    :param shape:
    :param points:
    :return:
    """

    for i, (pl, pr) in enumerate(zip(points[::2], points[1::2])):
        shape.controlPoints[i * 2].value = list(pl)[:-1]
        shape.controlPoints[i * 2 + 1].value = list(pr)[:-1]
