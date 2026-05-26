from maya import cmds
from maya.api import OpenMaya

from src.components._comp_base import MacroComponent
from src.rig.module.deferred_plug import DeferredPlug, MATRIX, FLOAT
from src.lib import guide
from src.rig.controls import control
from src.lib import naming
from src.lib import joint
from src.lib.nodes import Node


class FootRoll(MacroComponent):
    in_parent_mtx = DeferredPlug("parent_mtx", "input", MATRIX)
    in_local_toe_mtx = DeferredPlug("local_toe_mtx", "input", MATRIX)
    in_local_ball_mtx = DeferredPlug("local_toe_mtx", "input", MATRIX)
    in_roll_flt = DeferredPlug("local_toe_flt", "input", FLOAT)
    in_bank_flt = DeferredPlug("local_toe_flt", "input", FLOAT)
    in_ball_roll_compensate = DeferredPlug("in_ball_roll_compensate", "input", FLOAT)
    in_tip_start_rise = DeferredPlug("tip_start_rise", "input", FLOAT)
    in_tip_end_rise = DeferredPlug("tip_end_rise", "input", FLOAT)
    in_heel_twist = DeferredPlug("heel_twist", "input", FLOAT)
    in_ball_twist = DeferredPlug("ball_twist", "input", FLOAT)
    in_toe_twist = DeferredPlug("toe_twist", "input", FLOAT)

    out_mtxs = DeferredPlug("out_mtx", "output", MATRIX, multi=True)
    out_normalized_mtxs = DeferredPlug("out_normalized_mtx", "output", MATRIX, multi=True)

    def __init__(self, name: naming.Name):
        super().__init__(name)
        self.indices: list[str] = []
        self.bank_in_index: str | None = None
        self.bank_out_index: str | None = None
        self.bank_ball_index: str | None = None
        self.heel_index: str | None = None
        self.tip_index: str | None = None

    def build(self):
        ankle_mtx = OpenMaya.MMatrix(guide.get_world_matrix(self.name.replace(index=self.indices[0])))
        ball_mtx = OpenMaya.MMatrix(guide.get_world_matrix(self.name.replace(index=self.indices[1])))
        toe_mtx = OpenMaya.MMatrix(guide.get_world_matrix(self.name.replace(index=self.indices[2])))
        bank_in_mtx = OpenMaya.MMatrix(guide.get_world_matrix(self.name.replace(index=self.bank_in_index)))
        bank_ball_mtx = OpenMaya.MMatrix(guide.get_world_matrix(self.name.replace(index=self.bank_ball_index)))
        bank_out_mtx = OpenMaya.MMatrix(guide.get_world_matrix(self.name.replace(index=self.bank_out_index)))
        heel_mtx = OpenMaya.MMatrix(guide.get_world_matrix(self.name.replace(index=self.heel_index)))
        tip_mtx = OpenMaya.MMatrix(guide.get_world_matrix(self.name.replace(index=self.tip_index)))

        roll_chain = joint.create_chain(
            [bank_in_mtx, bank_out_mtx, heel_mtx, bank_ball_mtx, tip_mtx, toe_mtx, ball_mtx, ankle_mtx],
            self.name, False
        )
        cmds.parent(roll_chain[0], self.structure.logic)

        roll_chain[0].offsetParentMatrix.connect(self.in_parent_mtx.plug)

        condition = Node.create("condition", self.name.replace(index="bank", suffix="cond"))
        condition.firstTerm.connect(self.in_bank_flt.plug)
        condition.operation.value = 2  # >
        condition.colorIfTrue.value = [0, 0, 0]
        condition.colorIfFalse.value = [0, 0, 0]
        condition.colorIfTrueR.connect(self.in_bank_flt.plug)
        condition.colorIfFalseG.connect(self.in_bank_flt.plug)

        roll_chain[0].rz.connect(condition.outColorR)
        roll_chain[1].rz.connect(condition.outColorG)

        condition = Node.create("condition", self.name.replace(suffix="cond"))
        condition.firstTerm.connect(self.in_roll_flt.plug)
        condition.operation.value = 2  # >
        condition.colorIfTrue.value = [0, 0, 0]
        condition.colorIfFalse.value = [0, 0, 0]
        condition.colorIfTrueR.connect(self.in_roll_flt.plug)
        condition.colorIfFalseG.connect(self.in_roll_flt.plug)
        back_roll_plug = condition.outColorG
        fwd_roll_plug = condition.outColorR

        roll_chain[2].rx.connect(back_roll_plug)
        roll_chain[2].ry.connect(self.in_heel_twist.plug)

        clamp = Node.create("clampRange", self.name.replace(index="roll", suffix="clamp"))
        clamp.input.connect(fwd_roll_plug)
        clamp.maximum.connect(self.in_ball_roll_compensate.plug)
        roll_chain[3].rx.connect(clamp.output)
        roll_chain[3].ry.connect(self.in_ball_twist.plug)

        normalized_roll = Node.create("subtract", self.name.replace(suffix="minus"))
        normalized_roll.input1.connect(fwd_roll_plug)
        normalized_roll.input2.connect(clamp.output)

        factor = Node.create("divide", self.name.replace(suffix="div"))
        factor.input1.connect(self.in_tip_start_rise.plug)
        factor.input2.connect(self.in_tip_end_rise.plug)

        remap = Node.create("remapValue", self.name.replace(suffix="remap"))
        remap.inputValue.connect(normalized_roll.output)
        remap.inputMax.connect(self.in_tip_end_rise.plug)
        remap.outputMax.connect(self.in_tip_start_rise.plug)
        remap.value[0].value_Position.value = 0
        remap.value[0].value_FloatValue.value = 0
        remap.value[1].value_Position.connect(factor.output)
        remap.value[1].value_FloatValue.value = 1
        remap.value[2].value_Position.value = 1
        remap.value[2].value_FloatValue.value = 0

        roll_chain[6].rz.connect(remap.outValue)

        tip_roll = Node.create("subtract", self.name.replace(suffix="minus"))
        tip_roll.input1.connect(normalized_roll.output)
        tip_roll.input2.connect(remap.outValue)

        roll_chain[4].rx.connect(tip_roll.output)
        roll_chain[4].ry.connect(self.in_toe_twist.plug)

        self.out_mtxs.plug[0].connect(roll_chain[7].worldMatrix[0])
        self.out_mtxs.plug[1].connect(roll_chain[6].worldMatrix[0])
        self.out_mtxs.plug[2].connect(roll_chain[5].worldMatrix[0])

        self.out_normalized_mtxs.plug[0].connect(control.get_normalized_matrix_output(roll_chain[7]))
        self.out_normalized_mtxs.plug[1].connect(control.get_normalized_matrix_output(roll_chain[6]))
        self.out_normalized_mtxs.plug[2].connect(control.get_normalized_matrix_output(roll_chain[5]))
