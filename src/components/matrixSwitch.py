from maya import cmds
from maya.api import OpenMaya

from src.components._comp_base import MacroComponent
from src.lib import naming
from src.lib.nodes import Node
from src.rig.module.deferred_plug import MATRIX, FLOAT, DeferredPlug


class MatrixArraySwitch(MacroComponent):
    input_a_mtx = DeferredPlug("inA", "input", MATRIX, multi=True)
    input_b_mtx = DeferredPlug("inB", "input", MATRIX, multi=True)
    input_toggle = DeferredPlug("in_switch", "input", FLOAT)
    output = DeferredPlug("output", "output", MATRIX, multi=True)

    def __init__(self, name: naming.Name):
        super().__init__(name)
        self.default_value = OpenMaya.MMatrix()

    def build(self):
        a_indices = set(cmds.getAttr(self.input_a_mtx.plug, multiIndices=True) or [])
        b_indices = set(cmds.getAttr(self.input_b_mtx.plug, multiIndices=True) or [])
        all_indices = a_indices | b_indices

        default_plug = self.structure.input.add_attr("default", dt="matrix")

        for index in all_indices:
            a_plug = self.input_a_mtx.plug[index] if index in a_indices else default_plug
            b_plug = self.input_b_mtx.plug[index] if index in b_indices else default_plug

            choice_node = Node.create("choice", self.name.replace(suffix="choice", index=index))
            choice_node.selector.connect(self.input_toggle.plug)

            choice_node.input[0].connect(a_plug)
            choice_node.input[1].connect(b_plug)
            self.output.plug[index].connect(choice_node.output)
