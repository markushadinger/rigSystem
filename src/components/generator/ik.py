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


class IK(MacroComponent):
    in_parent_mtx = DeferredPlug("parent_mtx", "input", MATRIX)
    in_driver_mtx = DeferredPlug("driver_mtx", "input", MATRIX)
    in_pole_mtx = DeferredPlug("pole_mtx", "input", MATRIX)
    out_mtx = DeferredPlug("output_mtx", "output", MATRIX, multi=True)

    def __init__(self, name: naming.Name):
        super().__init__(name)

        self.pole_vector_distance = 10.0
        self.indices: list[str] = []
        self.pole_index: str | None = None
        self._additions = []

        self._joints: list[Node] | None = None

    def build(self):
        guide_matrices = [OpenMaya.MMatrix(guide.get_world_matrix(self.name.replace(index=i))) for i in self.indices]
        mid_mtx = OpenMaya.MMatrix(guide.get_world_matrix(self.name.replace(index=self.pole_index)))

        self.joints = joint.create_chain(
            matrices=guide_matrices,
            name=self.name.replace(suffix="jnt"),
            skin_joint=False
        )
        cmds.parent(self.joints[0], self.structure.logic)
        self.joints[0].offsetParentMatrix.connect(self.in_parent_mtx.plug)

        pole_mtx = Node.create("multMatrix", name=self.name.replace(suffix="mmlt"))
        pole_mtx.matrixIn[0].value = mid_mtx
        pole_mtx.matrixIn[1].connect(self.in_pole_mtx.plug)

        ik_handle, pole_constraint = ik.build_pole_ik(
            name=self.name.replace(extra="ik"),
            chain=self.joints,
            driver_plug=self.in_driver_mtx.plug,
            pole_plug=pole_mtx.matrixSum
        )
        cmds.parent(ik_handle, self.structure.logic)
        cmds.parent(pole_constraint, self.structure.logic)

        for i, jnt in enumerate(self.joints):
            self.out_mtx.plug[i].connect(control.get_normalized_matrix_output(jnt))

        LockTipSystem().build(self)


class LockTipSystem:
    def build(self, component: IK):
        tip_jnt = component.joints[-1]

        mmlt = Node.create("multMatrix", name=component.name.replace(suffix="mmlt"))
        mmlt.matrixIn[0].connect(component.in_driver_mtx.plug)
        mmlt.matrixIn[1].connect(tip_jnt.parentInverseMatrix[0])

        rot = Node.create("rotationFromMatrix", name=component.name.replace(suffix="mrot"))
        rot.input.connect(mmlt.matrixSum)
        tip_jnt.rotate.connect(rot.output)
