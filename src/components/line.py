from maya import cmds

from src.components._comp_base import MacroComponent
from src.lib.naming import Name
from src.rig.module.deferred_plug import MATRIX, DeferredPlug, BOOL
from src.lib.nodes import Node


class Line(MacroComponent):
    start_mtx = DeferredPlug("start_mtx", "input", MATRIX)
    in_visibility = DeferredPlug("start_mtx", "input", BOOL)
    end_mtx = DeferredPlug("end_mtx", "input", MATRIX)

    def __init__(self, name: Name):
        super().__init__(name)
        self.template: bool = True
        self.in_visibility.settings["dv"] = 1

    def build(self):
        curve = Node.generate(cmds.curve, name=str(self.name.replace(suffix="crv")), point=[(0, 0, 0)] * 2, degree=1)
        shape = Node(cmds.listRelatives(curve, shapes=True, children=True)[0])
        shape.template.value = self.template
        cmds.parent(curve, self.structure.controls)

        curve.visibility.connect(self.in_visibility.plug)

        start_pnt = Node.create("translationFromMatrix", self.name.replace(index="start", suffix="tmtx"))
        start_pnt.input.connect(self.start_mtx.plug)

        end_pnt = Node.create("translationFromMatrix", self.name.replace(index="end", suffix="tmtx"))
        end_pnt.input.connect(self.end_mtx.plug)

        shape.controlPoints[0].connect(start_pnt.output)
        shape.controlPoints[1].connect(end_pnt.output)
