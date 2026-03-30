from maya import cmds

from src.lib.nodes import Node, Plug


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

    def build(self):
        driver_plugs = []
        for mtx in self.in_matrix_plugs:
            trl = Node.create("translationFromMatrix", name=f"{self.surface_name}_{mtx.node}_tf")
            trl.input.connect(mtx)

            axis = Node.create("axisFromMatrix", name=f"{self.surface_name}_{mtx.node}_aim")
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

        knot_count_u = len(self.in_matrix_plugs)
        ku = get_k(self.degree, knot_count_u)
        self.out_surface_shape = Node.generate(
            cmds.surface,
            name=self.surface_name,
            du=self.degree,
            dv=1,
            ku=ku,
            kv=(0, 1),
            p=generate_placeholder_knots(knot_count_u, 2)
        )

        self.out_surface_transform = Node(cmds.listRelatives(self.out_surface_shape, parent=True)[0])
        shape_node = cmds.rename(str(self.out_surface_shape), f"{self.surface_name}Shape")
        self.out_surface_shape = Node(shape_node)

        for i, (l_plug, r_plug) in enumerate(driver_plugs):
            self.out_surface_shape.controlPoints[i * 2].connect(l_plug)
            self.out_surface_shape.controlPoints[i * 2 + 1].connect(r_plug)
