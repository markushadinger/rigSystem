from maya.api import OpenMaya

from src.components._comp_base import Component
from src.lib import naming
from src.lib.math import matrix
from src.lib.nodes import Node, Plug

from maya import cmds

TWIST_ROTATION_ORDER_MAPPING = {
    "x": 1,
    "y": 0,
    "z": 2,
}

VECTOR_MAPPING = {
    'x': [1, 0, 0],
    'y': [0, 1, 0],
    'z': [0, 0, 1],
}


class Piston(Component):

    def __init__(self, name: naming.Name):
        super().__init__(name)

        # -- inputs
        self.input_a: Plug = self.register_input("input_a", dt="matrix")
        self.input_b: Plug = self.register_input("input_b", dt="matrix")

        # --- outputs
        self.output_mtxs: Plug = self.register_output("outputs", dt="matrix", multi=True)

        # --- settings
        self.sample_count: int = 5
        self.aim_axis: str = 'x'
        self.start_up_axis: str = "z"
        self.end_up_axis: str = "z"
        self.up_axis: str = 'z'
        self.factors: list | None = None

    def build(self):
        super().build()

        factors = self.factors or [i / (self.sample_count - 1.0) for i in range(self.sample_count)]
        aim_vector = OpenMaya.MVector(VECTOR_MAPPING[self.aim_axis])

        start_up_vec = Node(self.name.replace(index="start", suffix="up")).create("axisFromMatrix")
        start_up_vec.axis.value = "xyz".index(self.start_up_axis)
        start_up_vec.input.connect(self.input_a)

        end_up_vec = Node(self.name.replace(index="end", suffix="up")).create("axisFromMatrix")
        end_up_vec.axis.value = "xyz".index(self.end_up_axis)
        end_up_vec.input.connect(self.input_b)

        start_aim_mtx = Node(self.name.replace(index="start", suffix="aim")).create("aimMatrix")
        start_aim_mtx.inputMatrix.connect(self.input_a)
        start_aim_mtx.primaryTargetMatrix.connect(self.input_b)
        start_aim_mtx.primaryInputAxis.value = aim_vector
        start_aim_mtx.primaryMode.value = 1
        start_aim_mtx.secondaryTargetVector.connect(start_up_vec.output)
        start_aim_mtx.secondaryInputAxis.value = VECTOR_MAPPING[self.up_axis]
        start_aim_mtx.secondaryMode.value = 2

        end_aim_mtx = Node(self.name.replace(index="end", suffix="aim")).create("aimMatrix")
        end_aim_mtx.inputMatrix.connect(self.input_b)
        end_aim_mtx.primaryTargetMatrix.connect(self.input_a)
        end_aim_mtx.primaryInputAxis.value = -aim_vector
        end_aim_mtx.primaryMode.value = 1
        end_aim_mtx.secondaryTargetVector.connect(end_up_vec.output)
        end_aim_mtx.secondaryInputAxis.value = VECTOR_MAPPING[self.up_axis]
        end_aim_mtx.secondaryMode.value = 2

        for i, factor in enumerate(factors):
            blend = Node(self.name.replace(index=i, suffix="blend")).create("blendMatrix")
            blend.inputMatrix.connect(start_aim_mtx.outputMatrix)
            blend.target[0].targetMatrix.connect(end_aim_mtx.outputMatrix)
            blend.target[0].weight.value = factor

            self.output_mtxs[i].connect(blend.outputMatrix)
