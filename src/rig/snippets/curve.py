from maya import cmds

from src.lib.nodes import Node, Plug
from src.rig.controls import shape


class MatrixDrivenCurveBuilder:
    def __init__(self):
        self.name: str = "curve"
        self.degree: int = 3

        self.in_matrix_plugs: list[Plug] = []
        self.our_transform_node: Node | None = None
        self.out_shape_node: Node | None = None

    def build(self):

        trf_plugs = []

        for mtx_plug in self.in_matrix_plugs:
            trl = Node.create("translationFromMatrix", name=f"{self.name}_{mtx_plug.node}_tf")
            trl.input.connect(mtx_plug)
            trf_plugs.append(trl.output)

        self.our_transform_node = Node.generate(
            cmds.curve,
            name=self.name,
            degree=self.degree,
            p=[(0, 0, 0)] * len(self.in_matrix_plugs)
        )

        self.out_shape_node = shape.get_shape_node(self.our_transform_node)

        for i, trf_plug in enumerate(trf_plugs):
            self.out_shape_node.controlPoints[i].connect(trf_plug)
