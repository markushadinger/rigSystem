from maya import cmds
from maya.api import OpenMaya

from src.components._comp_base import MacroComponent
from src.rig.module.deferred_plug import DeferredPlug, MATRIX
from src.lib import guide
from src.rig.controls import control
from src.lib import naming
from src.lib import joint
from src.lib.nodes import Node
from src.rig.snippets import ik


class FootRoll(MacroComponent):
    in_parent_mtx = DeferredPlug("parent_mtx", "input", MATRIX)
    out_mtxs = DeferredPlug("out_mtx", "output", MATRIX, multi=True)
    out_normalized_mtxs = DeferredPlug("out_normalized_mtx", "output", MATRIX, multi=True)

    def __init__(self, name: naming.Name):
        super().__init__(name)
        self.indices: list[str] = []

    def build(self):
        guide_matrices = [OpenMaya.MMatrix(guide.get_world_matrix(self.name.replace(index=i))) for i in self.indices]



