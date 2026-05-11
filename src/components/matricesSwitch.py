from maya import cmds
from maya.api import OpenMaya

from src.components._comp_base import MacroComponent
from src.lib import naming
from src.lib.nodes import Node
from src.rig.module.deferred_plug import MATRIX, FLOAT, DeferredPlug


class MatricesSwitch(MacroComponent):
    in_a_mtxs = DeferredPlug("inA", "input", MATRIX, multi=True)
    in_b_mtxs = DeferredPlug("inB", "input", MATRIX, multi=True)
    in_switch_bool = DeferredPlug("in_switch", "input", FLOAT)
    out_mtxs = DeferredPlug("output", "output", MATRIX, multi=True)

    def __init__(self, name: naming.Name):
        super().__init__(name)
        self.default_value = OpenMaya.MMatrix()

    def build(self):
        a_indices = set(self.in_a_mtxs.plug.connected_indices())
        b_indices = set(self.in_b_mtxs.plug.connected_indices())
        all_indices = a_indices | b_indices

        default_plug = self.structure.input.add_attr("default", dt="matrix")

        for index in all_indices:
            a_plug = self.in_a_mtxs.plug[index] if index in a_indices else default_plug
            b_plug = self.in_b_mtxs.plug[index] if index in b_indices else default_plug

            choice_node = Node.create("choice", self.name.replace(suffix="choice", index=index))
            choice_node.selector.connect(self.in_switch_bool.plug)

            choice_node.input[0].connect(a_plug)
            choice_node.input[1].connect(b_plug)
            self.out_mtxs.plug[index].connect(choice_node.output)
