from maya.api import OpenMaya

from src.components._comp_base import MacroComponent
from src.rig.module.deferred_plug import DeferredPlug, MATRIX
from src.lib import guide
from src.lib import naming
from src.lib.nodes import Node

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


class Piston(MacroComponent):
    in_start_mtx = DeferredPlug("start_mtx", "input", MATRIX)
    in_end_mtx = DeferredPlug("end_mtx", "input", MATRIX)

    out_mtxs = DeferredPlug("end_orient", "output", MATRIX, multi=True)

    def __init__(self, name: naming.Name):
        super().__init__(name)
        self.indices: list[str] = []
        self.sample_count: int = 5
        self.aim_vector: str = 'x'
        self.start_up_axis: str = "z"
        self.end_up_axis: str = "z"
        self.up_vector: str = 'z'

        self.factors: list | None = None

    def build(self):
        start_mtx = OpenMaya.MMatrix(guide.get_world_matrix(self.name.replace(index=self.indices[0])))
        end_mtx = OpenMaya.MMatrix(guide.get_world_matrix(self.name.replace(index=self.indices[1])))
        factors = self.factors or [i / (self.sample_count - 1.0) for i in range(self.sample_count)]

        normalized_end_mtx = OpenMaya.MMatrix(list(start_mtx)[:12] + list(end_mtx)[12:])

        start_mmlt = Node.create("multMatrix", self.name.replace(suffix="mmlt", index="start"))
        start_mmlt.matrixIn[0].value = start_mtx
        start_mmlt.matrixIn[1].connect(self.in_start_mtx.plug)

        end_mmlt = Node.create("multMatrix", self.name.replace(suffix="mmlt", index="end"))
        end_mmlt.matrixIn[0].value = normalized_end_mtx
        end_mmlt.matrixIn[1].connect(self.in_end_mtx.plug)

        start_vector = Node.create("axisFromMatrix", self.name.replace(index="upStart", suffix="axis"))
        start_vector.input.connect(start_mmlt.matrixSum)
        start_vector.axis.value = "xyz".index(self.start_up_axis)

        start_aim_mtx = Node.create("aimMatrix", self.name.replace(suffix="aim", index="start"))
        start_aim_mtx.inputMatrix.connect(start_mmlt.matrixSum)
        start_aim_mtx.primaryTargetMatrix.connect(end_mmlt.matrixSum)
        start_aim_mtx.primaryInputAxis.value = VECTOR_MAPPING[self.aim_vector]
        start_aim_mtx.primaryMode.value = 1
        start_aim_mtx.secondaryTargetVector.connect(start_vector.output)
        start_aim_mtx.secondaryInputAxis.value = VECTOR_MAPPING[self.up_vector]
        start_aim_mtx.secondaryMode.value = 2

        end_vector = Node.create("axisFromMatrix", self.name.replace(index="upEnd", suffix="axis"))
        end_vector.input.connect(end_mmlt.matrixSum)
        end_vector.axis.value = "xyz".index(self.end_up_axis)

        end_aim_mtx = Node.create("aimMatrix", self.name.replace(suffix="aim", index="end"))
        end_aim_mtx.inputMatrix.connect(end_mmlt.matrixSum)
        end_aim_mtx.primaryTargetMatrix.connect(start_mmlt.matrixSum)
        end_aim_mtx.primaryInputAxis.value = [-v for v in VECTOR_MAPPING[self.aim_vector]]
        end_aim_mtx.primaryMode.value = 1
        end_aim_mtx.secondaryTargetVector.connect(end_vector.output)
        end_aim_mtx.secondaryInputAxis.value = VECTOR_MAPPING[self.up_vector]
        end_aim_mtx.secondaryMode.value = 2

        inverse_aim = Node.create("inverseMatrix", self.name.replace(suffix="inverse"))
        inverse_aim.inputMatrix.connect(start_aim_mtx.outputMatrix)

        end_local_mmlt = Node.create("multMatrix", self.name.replace(suffix="mmlt", index="localEnd"))
        end_local_mmlt.matrixIn[0].connect(end_aim_mtx.outputMatrix)
        end_local_mmlt.matrixIn[1].connect(inverse_aim.outputMatrix)

        decompose_local_end = Node.create("decomposeMatrix", self.name.replace(suffix="dcmp"))
        decompose_local_end.inputMatrix.connect(end_local_mmlt.matrixSum)
        decompose_local_end.inputRotateOrder.value = TWIST_ROTATION_ORDER_MAPPING[self.aim_vector]

        for i in range(self.sample_count):
            blend_trf = Node.create("multiplyDivide", self.name.replace(index=i, suffix="trfBlend"))
            blend_trf.input1.value = [factors[i]] * 3
            blend_trf.input2.connect(decompose_local_end.ot)

            blend_rx = Node.create("multiply", self.name.replace(index=i, suffix="rBlend"))
            blend_rx.input[0].value = factors[i]
            blend_rx.input[1].connect(decompose_local_end.orx)

            compose_mtx = Node.create("composeMatrix", self.name.replace(index=i, suffix="comp"))
            compose_mtx.it.connect(blend_trf.output)
            compose_mtx.irx.connect(blend_rx.output)

            blend_mtx = Node.create("multMatrix", self.name.replace(suffix="mmlt", index="localEnd"))
            blend_mtx.matrixIn[0].connect(compose_mtx.outputMatrix)
            blend_mtx.matrixIn[1].connect(start_aim_mtx.outputMatrix)

            self.out_mtxs.plug[i].connect(blend_mtx.matrixSum)
