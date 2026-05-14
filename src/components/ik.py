import math

from maya import cmds
from maya.api import OpenMaya

from src.components._comp_base import MacroComponent
from src.rig.module.deferred_plug import DeferredPlug, MATRIX, FLOAT
from src.lib import guide
from src.rig.controls import control
from src.lib.naming import Name
from src.lib import joint
from src.lib.nodes import Node
from src.rig.snippets import ik

from src.lib.math import matrix


class IK(MacroComponent):
    in_parent_mtx = DeferredPlug("parent_mtx", "input", MATRIX)
    in_driver_mtx = DeferredPlug("driver_mtx", "input", MATRIX)
    in_pole_mtx = DeferredPlug("pole_mtx", "input", MATRIX)
    in_stretch_flt = DeferredPlug("stretch_flt", "input", FLOAT, multi=True)

    out_mtx = DeferredPlug("out_mtx", "output", MATRIX, multi=True)
    out_normalized_mtx = DeferredPlug("out_normalized_mtx", "output", MATRIX, multi=True)

    def __init__(self, name: Name):
        super().__init__(name)

        self.pole_vector_distance = 10.0
        self.indices: list[str] = []
        self.pole_index: str | None = None
        self._additions = []

        self._joints: list[Node] | None = None

    def build(self):

        self._build_chain()

        ik_handle, pole_constraint = ik.build_pole_ik(
            name=self.name.replace(extra="ik"),
            chain=self.joints,
            driver_plug=self.in_driver_mtx.plug,
            pole_plug=self.in_pole_mtx.plug
        )
        cmds.parent(ik_handle, self.structure.logic)
        cmds.parent(pole_constraint, self.structure.logic)

        for i, jnt in enumerate(self.joints):
            self.out_normalized_mtx.plug[i].connect(control.get_normalized_matrix_output(jnt))
            self.out_mtx.plug[i].connect(jnt.worldMatrix[0])

        self._setup_stretch()

    def _build_chain(self):
        """
        build the joint chain
        :return:
        """

        guide_matrices = [OpenMaya.MMatrix(guide.get_world_matrix(self.name.replace(index=i))) for i in self.indices]

        self.joints = joint.create_chain(
            matrices=guide_matrices,
            name=self.name.replace(suffix="jnt"),
            skin_joint=False
        )
        cmds.parent(self.joints[0], self.structure.logic)
        self.joints[0].offsetParentMatrix.connect(self.in_parent_mtx.plug)

    def _setup_stretch(self):
        """
        connect the stretch attributes to the joints.
        ignore inputs that are not connected
        :return:
        """
        stretch_indices = self.in_stretch_flt.plug.connected_indices()
        for i, index in enumerate(self.indices[1:]):
            if i not in stretch_indices:
                continue

            jnt = self.joints[i + 1]

            stretch_node = Node.create("multiplyDivide", self.name.replace(suffix="div", index=index))
            stretch_node.input1.value = jnt.t.value[0]
            stretch_node.input2X.connect(self.in_stretch_flt.plug[i])
            stretch_node.input2Y.connect(self.in_stretch_flt.plug[i])
            stretch_node.input2Z.connect(self.in_stretch_flt.plug[i])
            jnt.t.connect(stretch_node.output)


class Stretch(MacroComponent):
    in_start_mtx = DeferredPlug("in_end_mtx", "input", MATRIX)
    in_end_mtx = DeferredPlug("in_end_mtx", "input", MATRIX)
    in_inv_scale_mtx = DeferredPlug("in_inverse_mtx", "input", MATRIX)
    in_custom_stretch = DeferredPlug("in_custom_stretch", "input", FLOAT, multi=True)
    in_soft_radius = DeferredPlug("in_soft_radius", "input", FLOAT)
    out_length_flts = DeferredPlug("out_flts", "output", FLOAT, multi=True)

    def __init__(self, name: Name):
        super().__init__(name)

        self.indices: list = []
        self.enable_soft_ik = True

    def build(self):
        guide_matrices = [OpenMaya.MMatrix(guide.get_world_matrix(self.name.replace(index=i))) for i in self.indices]
        points = [matrix.get_point_from_matrix(m) for m in guide_matrices]
        distances = [p1.distanceTo(p2) for p1, p2 in zip(points, points[1:])]

        chain_length = Node.create("sum", self.name.replace(suffix="sum"))
        custom_indices = self.in_custom_stretch.plug.connected_indices()
        mult_plugs = []
        for i, index in enumerate(self.indices[1:]):
            if i in custom_indices:
                mult = Node.create("multiply", self.name.replace(suffix="mult", index=index))
                mult.input[0].value = distances[i]
                mult.input[1].connect(self.in_custom_stretch.plug[i])
                chain_length.input[i].connect(mult.output)
                mult_plugs.append(mult.output)
            else:
                chain_length.input[i].value = distances
                mult_plugs.append(None)

        start_mmlt = Node.create("multMatrix", self.name.replace(suffix="mmlt", index="start"))
        start_mmlt.matrixIn[0].value = guide_matrices[0]
        start_mmlt.matrixIn[1].connect(self.in_start_mtx.plug)
        start_mmlt.matrixIn[2].connect(self.in_inv_scale_mtx.plug)

        end_mmlt = Node.create("multMatrix", self.name.replace(suffix="mmlt", index="end"))
        end_mmlt.matrixIn[0].value = guide_matrices[-1]
        end_mmlt.matrixIn[1].connect(self.in_end_mtx.plug)
        end_mmlt.matrixIn[2].connect(self.in_inv_scale_mtx.plug)

        control_distance = Node.create("distanceBetween", self.name.replace(suffix="distance"))
        control_distance.inMatrix1.connect(start_mmlt.matrixSum)
        control_distance.inMatrix2.connect(end_mmlt.matrixSum)

        if self.enable_soft_ik:
            soft_start = Node.create("subtract", self.name.replace(index="soft", suffix="minus"))
            soft_start.input1.connect(chain_length.output)
            soft_start.input2.connect(self.in_soft_radius.plug)

            exp_length = Node.create("subtract", self.name.replace(index="soft", suffix="minus"))
            exp_length.input1.connect(control_distance.distance)
            exp_length.input2.connect(soft_start.output)

            exp_divide = Node.create("divide", self.name.replace(index="soft", suffix="div"))
            exp_divide.input1.connect(exp_length.output)
            exp_divide.input2.connect(self.in_soft_radius.plug)

            neg_mult = Node.create("multiply", self.name.replace(index="soft", suffix="mult"))
            neg_mult.input[0].connect(exp_divide.output)
            neg_mult.input[1].value = -1

            power = Node.create("power", self.name.replace(index="soft", suffix="pow"))
            power.input.value = math.e
            power.exponent.connect(neg_mult.output)

            one_minus = Node.create("subtract", self.name.replace(index="soft", suffix="minus"))
            one_minus.input1.value = 1
            one_minus.input2.connect(power.output)

            neg_mult = Node.create("multiply", self.name.replace(index="soft", suffix="mult"))
            neg_mult.input[0].connect(one_minus.output)
            neg_mult.input[1].connect(self.in_soft_radius.plug)

            soft_distance = Node.create("sum", self.name.replace(index="soft", suffix="sum"))
            soft_distance.input[0].connect(neg_mult.output)
            soft_distance.input[1].connect(soft_start.output)

            condition = Node.create("condition", self.name.replace(index="soft", suffix="cond"))
            condition.firstTerm.connect(control_distance.distance)
            condition.secondTerm.connect(soft_start.output)
            condition.operation.value = 4  # <
            condition.colorIfTrueR.connect(control_distance.distance)
            condition.colorIfFalseR.connect(soft_distance.output)

            factor = Node.create("divide", self.name.replace(suffix="div"))
            factor.input1.connect(control_distance.distance)
            factor.input2.connect(condition.outColorR)
            stretch_plug = factor.output

        else:
            factor = Node.create("divide", self.name.replace(suffix="div"))
            factor.input1.connect(control_distance.distance)
            factor.input2.connect(chain_length.output)
            stretch_plug = factor.output

        maximum = Node.create("max", self.name.replace(suffix="max"))
        maximum.input[0].value = 1
        maximum.input[1].connect(stretch_plug)

        for i, index in enumerate(self.indices[1:]):
            out_plug = maximum.output

            if i in custom_indices:
                final_mult = Node.create("multiply", self.name.replace(index=index, suffix="mult"))
                final_mult.input[0].connect(out_plug)
                final_mult.input[1].connect(self.in_custom_stretch.plug[i])
                out_plug = final_mult.output

            self.out_length_flts.plug[i].connect(out_plug)


class LockTipSystem:
    def build(self, component: IK):
        tip_jnt = component.joints[-1]

        mmlt = Node.create("multMatrix", name=component.name.replace(suffix="mmlt"))
        mmlt.matrixIn[0].connect(component.in_driver_mtx.plug)
        mmlt.matrixIn[1].connect(tip_jnt.parentInverseMatrix[0])

        rot = Node.create("rotationFromMatrix", name=component.name.replace(suffix="mrot"))
        rot.input.connect(mmlt.matrixSum)
        tip_jnt.rotate.connect(rot.output)
