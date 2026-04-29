from maya import cmds

from src.components._comp_base import MacroComponent
from src.lib import naming
from src.rig.module.deferred_plug import MATRIX, DeferredPlug
from src.lib import joint
from src.lib import guide


class JointRenderer(MacroComponent):
    input = DeferredPlug("input", "input", MATRIX, multi=True)
    output = DeferredPlug("output", "output", MATRIX, multi=True)

    def __init__(self, name: naming.Name):
        super().__init__(name)
        self.indices: list[str | None] = [None]
        self.nice_name: naming.Name = self.name
        self.for_skinning: bool = False

    def build(self):
        for i, index in enumerate(self.indices):
            jnt = joint.create(self.nice_name.replace(index=index), skin_joint=self.for_skinning)
            cmds.parent(jnt, self.structure.deform if self.for_skinning else self.structure.logic)

            jnt.offsetParentMatrix.connect(self.input.plug[i])
            cmds.xform(jnt, worldSpace=True, matrix=guide.get_world_matrix(self.name.replace(index=index)))
