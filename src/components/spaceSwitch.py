from src.components._comp_base import MacroComponent
from src.rig.module.deferred_plug import DeferredPlug, MATRIX, INT8
from src.lib import guide
from src.lib import naming
from src.lib.nodes import Node


class SpaceSwitch(MacroComponent):
    parent_mtx = DeferredPlug("parent_mtx", "input", MATRIX)
    target_mtxs = DeferredPlug("target_mtx", "input", MATRIX, multi=True)
    switch_int = DeferredPlug("switch_int", "input", INT8)
    out_mtx = DeferredPlug("end_orient", "output", MATRIX)

    def __init__(self, name: naming.Name):
        super().__init__(name)
        self.index: str = ""
        self.rotation: bool = False
        self.translation: bool = False
        self.scale: bool = False

    def build(self):
        guide_mtx = guide.get_world_matrix(self.name.replace(index=self.index))

        choice = Node.create("choice", self.name.replace(suffix="choice"))
        choice.selector.connect(self.switch_int.plug)

        for i, index in enumerate(self.target_mtxs.plug.connected_indices()):
            mmlt = Node.create("multMatrix", self.name.replace(index=index, suffix="mmlt"))
            mmlt.matrixIn[0].value = guide_mtx
            mmlt.matrixIn[1].connect(self.target_mtxs.plug[index])
            choice.input[i].connect(mmlt.matrixSum)

        parent_mmlt = Node.create("multMatrix", self.name.replace(index="parent", suffix="mmlt"))
        parent_mmlt.matrixIn[0].value = guide_mtx
        parent_mmlt.matrixIn[1].connect(self.parent_mtx.plug)

        blend_mtx = Node.create("blendMatrix", self.name.replace(suffix="blend"))
        blend_mtx.inputMatrix.connect(parent_mmlt.matrixSum)
        blend_mtx.target[0].targetMatrix.connect(choice.output)
        blend_mtx.target[0].rotateWeight.value = self.rotation
        blend_mtx.target[0].translateWeight.value = self.translation
        blend_mtx.target[0].scaleWeight.value = self.scale

        norm_mmlt = Node.create("multMatrix", self.name.replace(index="norm", suffix="mmlt"))
        norm_mmlt.matrixIn[0].value = guide_mtx.inverse()
        norm_mmlt.matrixIn[1].connect(blend_mtx.outputMatrix)

        self.out_mtx.plug.connect(norm_mmlt.matrixSum)
