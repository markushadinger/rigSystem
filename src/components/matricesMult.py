from src.components._comp_base import MacroComponent
from src.lib.nodes import Node
from src.rig.module.deferred_plug import MATRIX, DeferredPlug


class MatricesMult(MacroComponent):
    in_mtxs = DeferredPlug("in", "input", MATRIX, multi=True)
    in_parent_mtx = DeferredPlug("in_parent", "input", MATRIX)
    out_mtxs = DeferredPlug("out", "output", MATRIX, multi=True)

    def build(self):

        for index in self.in_mtxs.plug.connected_indices():
            in_plug = self.in_mtxs.plug[index]

            mmlt_node = Node.create("multMatrix", self.name.replace(suffix="mmlt", index=index))
            mmlt_node.matrixIn[0].connect(in_plug)
            mmlt_node.matrixIn[1].connect(self.in_parent_mtx.plug)
            self.out_mtxs.plug[index].connect(mmlt_node.matrixSum)
