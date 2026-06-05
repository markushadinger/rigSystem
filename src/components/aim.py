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


class Aim(MacroComponent):
    in_mtx = DeferredPlug("in_mtx", "input", MATRIX)
    target_mtx = DeferredPlug("target_mtx", "input", MATRIX)
    up_mtx = DeferredPlug("up_mtx", "input", MATRIX)
    out_mtx = DeferredPlug("out_mtx", "output", MATRIX)

    def __init__(self, name: naming.Name):
        super().__init__(name)
        self.aim_vector: str = 'x'
        self.up_vector: str = "z"

    def build(self):

        up_axis = Node.create("axisFromMatrix", self.name.replace(suffix="axis"))
        up_axis.input.connect(self.up_mtx.plug)
        up_axis.axis.value = "xyz".index(self.up_vector)

        aim_mtx = Node.create("aimMatrix", self.name.replace(suffix="aim"))
        aim_mtx.inputMatrix.connect(self.in_mtx.plug)
        aim_mtx.primaryTargetMatrix.connect(self.target_mtx.plug)
        aim_mtx.primaryInputAxis.value = VECTOR_MAPPING[self.aim_vector]
        aim_mtx.primaryMode.value = 1
        aim_mtx.secondaryTargetVector.connect(up_axis.output)
        aim_mtx.secondaryInputAxis.value = VECTOR_MAPPING[self.up_vector]
        aim_mtx.secondaryMode.value = 2
        self.out_mtx.plug.connect(aim_mtx.outputMatrix)
