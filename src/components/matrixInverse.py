from maya import cmds

from src.components._comp_base import MacroComponent
from src.lib import naming
from src.lib.nodes import Node
from src.rig.module.deferred_plug import MATRIX, DeferredPlug


class MatrixInverse(MacroComponent):
    in_mtx = DeferredPlug("in", "input", MATRIX)
    out_mtx = DeferredPlug("out", "output", MATRIX)

    def build(self):
        inverse = Node.create("inverseMatrix", self.name.replace(suffix="minv"))
        inverse.inputMatrix.connect(self.in_mtx.plug)
        self.out_mtx.plug.connect(inverse.outputMatrix)
