from maya.api import OpenMaya

from src.components._comp_base import MacroComponent
from src.lib import guide
from src.lib.nodes import Node
from src.lib.naming import Name
from src.rig.module.deferred_plug import MATRIX, DeferredPlug, FLOAT


class MatrixBlend(MacroComponent):
    in_mtx = DeferredPlug("in_base", "input", MATRIX)
    in_blend = DeferredPlug("in_blend", "input", MATRIX)
    in_blend_rotate = DeferredPlug("in_blend_rotate", "input", FLOAT)
    in_blend_translate = DeferredPlug("in_blend_rotate", "input", FLOAT)
    in_blend_scale = DeferredPlug("in_blend_rotate", "input", FLOAT)
    out_mtx = DeferredPlug("out", "output", MATRIX)

    def build(self):
        blend_mtx = Node.create("blendMatrix", self.name.replace(index="local", suffix="mblend"))
        blend_mtx.inputMatrix.connect(self.in_mtx.plug)
        blend_mtx.target[0].targetMatrix.connect(self.in_blend.plug)
        blend_mtx.target[0].rotateWeight.connect(self.in_blend_rotate.plug)
        blend_mtx.target[0].translateWeight.connect(self.in_blend_translate.plug)
        blend_mtx.target[0].scaleWeight.connect(self.in_blend_scale.plug)
        self.out_mtx.plug.connect(blend_mtx.outputMatrix)


class MatrixLocalBlend(MatrixBlend):

    def __init__(self, name: Name):
        super().__init__(name)

        self.maintain_offset: bool = True

    def build(self):
        inverse_mtx = Node.create("inverseMatrix", self.name.replace(index="local", suffix="minv"))
        inverse_mtx.inputMatrix.connect(self.in_mtx.plug)

        local_mtx = Node.create("multMatrix", self.name.replace(index="local", suffix="mmlt"))
        local_mtx.matrixIn[0].connect(self.in_blend.plug)
        local_mtx.matrixIn[1].connect(inverse_mtx.outputMatrix)

        blend_mtx = Node.create("blendMatrix", self.name.replace(index="local", suffix="mblend"))
        blend_mtx.inputMatrix.value = local_mtx.matrixSum.value if self.maintain_offset else OpenMaya.MMatrix.kIdentity
        blend_mtx.target[0].targetMatrix.connect(local_mtx.matrixSum)
        blend_mtx.target[0].rotateWeight.connect(self.in_blend_rotate.plug)
        blend_mtx.target[0].translateWeight.connect(self.in_blend_translate.plug)
        blend_mtx.target[0].scaleWeight.connect(self.in_blend_scale.plug)

        global_mtx = Node.create("multMatrix", self.name.replace(index="local", suffix="mmlt"))
        global_mtx.matrixIn[0].connect(blend_mtx.outputMatrix)
        global_mtx.matrixIn[1].connect(self.in_mtx.plug)

        self.out_mtx.plug.connect(global_mtx.matrixSum)


class MatrixNormalBlend(MatrixBlend):

    def __init__(self, name: Name):
        super().__init__(name)

        self.index: bool = True

    def build(self):
        guide_mtx = guide.get_world_matrix(self.name.replace(index=self.index))

        base_mtx = Node.create("multMatrix", self.name.replace(index="local", suffix="mmlt"))
        base_mtx.matrixIn[0].value = guide_mtx
        base_mtx.matrixIn[1].connect(self.in_mtx.plug)

        target_mtx = Node.create("multMatrix", self.name.replace(index="local", suffix="mmlt"))
        target_mtx.matrixIn[0].value = guide_mtx
        target_mtx.matrixIn[1].connect(self.in_blend.plug)

        blend_mtx = Node.create("blendMatrix", self.name.replace(index="local", suffix="mblend"))
        blend_mtx.inputMatrix.connect(base_mtx.matrixSum)
        blend_mtx.target[0].targetMatrix.connect(target_mtx.matrixSum)
        blend_mtx.target[0].rotateWeight.connect(self.in_blend_rotate.plug)
        blend_mtx.target[0].translateWeight.connect(self.in_blend_translate.plug)
        blend_mtx.target[0].scaleWeight.connect(self.in_blend_scale.plug)

        global_mtx = Node.create("multMatrix", self.name.replace(index="local", suffix="mmlt"))
        global_mtx.matrixIn[0].value = guide_mtx.inverse()
        global_mtx.matrixIn[1].connect(blend_mtx.outputMatrix)

        self.out_mtx.plug.connect(global_mtx.matrixSum)
