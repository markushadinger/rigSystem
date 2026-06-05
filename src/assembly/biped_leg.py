from maya.api import OpenMaya

from src.architecture import builder
from src.components.offset_systems.ankleIkOffsetSystem import AnkleIkOffsetSystem
from src.components.offset_systems.poleVectorOffsetSystem import PoleVectorOffsetSystem
from src.components.matricesSwitch import MatricesSwitch
from src.components.jointRenderer import JointRenderer
from src.assembly.basic.fk_chain import FkChain
from src.components._comp_base import Component
from src.components.footRoll import FootRoll
from src.components.matricesMult import MatricesMult
from src.components.piston import Piston
from src.components.spaceSwitch import SpaceSwitch
from src.components.mathFloat import OneMinus, Max
from src.rig.module.deferred_plug import DeferredPlug, MATRIX
from src.components.line import Line
from src.components import control, ik
from src.lib import constants
from src.lib.naming import Name
from src.rig.controls import shape


class BipedLeg(builder.Builder):
    INDICES = ["leg", "knee", "ankle", "ball", "toe"]

    def __init__(self, name: Name):
        super().__init__(name)

        self.color = shape.SIDE_COLOR[self.name.side]
        self.ik_shape = shape.ShapeData(
            points=shape.scale(shape.CUBE, 5),
            color=self.color,
            degree=1)

        self.switch_shape = shape.ShapeData(
            points=shape.translate(shape.scale(shape.DROPLET, [3, 3, -3]), [0, 0, 10]),
            color=self.color,
            degree=1)

        self.fk_shape = shape.ShapeData(
            points=shape.rotate(shape.scale(shape.CIRCLE, 10), [0, 0, 90]),
            color=self.color,
            degree=1)

        self.structure = Component(self.name)
        self.in_global = self.structure.add_deferred_plug(DeferredPlug("in_global", "input", MATRIX))
        self.in_localize = self.structure.add_deferred_plug(DeferredPlug("in_localize", "input", MATRIX))
        self.in_parent = self.structure.add_deferred_plug(DeferredPlug("in_parent", "input", MATRIX))
        self.in_local_parent = self.structure.add_deferred_plug(DeferredPlug("in_parent_local", "input", MATRIX))
        self.add_module(self.structure)

        self.switch = control.ControlGenerator(self.name.replace(extra="switch"))
        self.switch.index = self.INDICES[2]
        self.switch.external_structure = self.structure.structure
        self.switch.default_shape = self.switch_shape
        self.switch.remove_attr(*constants.ATTR_TRF)
        self.fk_ik_attr = self.switch.add_attr("fk_ik", at="short", min=0, max=1, k=True, dv=1)
        self.show_fk = self.switch.add_attr("show_fk", at="bool", k=False, dv=0)
        self.show_ik = self.switch.add_attr("show_ik", at="bool", k=False, dv=0)
        self.add_module(self.switch)

        self.fk_vis_invert = OneMinus(self.name.replace(extra="fkVisInvert"))
        self.fk_vis_invert.in_flt.connect(self.fk_ik_attr)
        self.add_module(self.fk_vis_invert)

        self.fk_vis = Max(self.name.replace(extra="fkVis"))
        self.fk_vis.in_flt.connect(self.fk_vis_invert.out_flt, dst_index=0)
        self.fk_vis.in_flt.connect(self.show_fk, dst_index=1)
        self.add_module(self.fk_vis)

        self.ik_vis = Max(self.name.replace(extra="ikVis"))
        self.ik_vis.in_flt.connect(self.fk_ik_attr, dst_index=0)
        self.ik_vis.in_flt.connect(self.show_ik, dst_index=1)
        self.add_module(self.ik_vis)

        self.fk_spsw = SpaceSwitch(self.name.replace(extra="fkSpSw"))
        self.fk_spsw.parent_mtx.connect(self.in_parent)
        self.fk_spsw.index = self.INDICES[0]
        self.fk_spsw.rotation = True
        self.add_module(self.fk_spsw)

        # --- fk

        self.fk = FkChain(self.name.replace(extra="fk"))
        self.fk.in_mtx.connect(self.fk_spsw.out_mtx)
        self.fk.in_visibility.connect(self.fk_vis.out_flt)
        self.fk.indices = self.INDICES
        self.fk.structure.external_structure = self.structure.structure
        self.fk.default_shape = self.fk_shape
        self.fk.for_skinning = True
        self.fk.indices_without_shape = self.INDICES[-1:]
        self.fk.init_submodules()
        self.add_module(self.fk)

        self.fk_spsw_attr = self.fk.fk_modules[0].add_attr("space", at="enum", k=True, dv=0, en="-")
        self.fk_spsw.switch_int.connect(self.fk_spsw_attr)

        # --- ik

        self.ik_spsw = SpaceSwitch(self.name.replace(extra="ikSpSw"))
        self.ik_spsw.parent_mtx.connect(self.in_global)
        self.ik_spsw.index = self.INDICES[2]
        self.ik_spsw.rotation = True
        self.ik_spsw.translation = True
        self.add_module(self.ik_spsw)

        ik_offset = AnkleIkOffsetSystem(self.name.replace(extra="tPoseOffset"))
        ik_offset.aim_vector = OpenMaya.MVector.kYaxisVector
        ik_offset.aim_axis = "y"
        ik_offset.up_axis = "z"
        ik_offset.hip_index = self.INDICES[0]

        self.ik_handle = control.ControlGenerator(self.name.replace(extra="ik", index=self.INDICES[2]))
        self.ik_handle.set_offset_system(ik_offset)
        self.ik_handle.in_parent_mtx.connect(self.ik_spsw.out_mtx)
        self.ik_handle.in_visibility.connect(self.ik_vis.out_flt)
        self.ik_handle.index = self.INDICES[2]
        self.ik_handle.external_structure = self.structure.structure
        self.ik_handle.default_shape = shape.ShapeData(
            points=shape.scale(shape.CUBE, 5),
            color=self.color,
            degree=1
        )
        self.ik_spsw_attr = self.ik_handle.add_attr("space", at="enum", k=True, dv=0, en="-")
        self.ik_handle.add_seperator("Stretch")
        self.upper_stretch = self.ik_handle.add_attr("upperStretch", at="float", k=True, dv=1, min=0.01)
        self.lower_stretch = self.ik_handle.add_attr("lowerStretch", at="float", k=True, dv=1, min=0.01)
        self.ik_handle.add_seperator("Roll")
        self.roll_attr = self.ik_handle.add_attr("roll", at="float", k=True)
        self.bank_attr = self.ik_handle.add_attr("bank", at="float", k=True)
        self.ik_handle.add_seperator("Twist")
        self.heel_twist = self.ik_handle.add_attr("heelTwist", at="float", k=True)
        self.ball_twist = self.ik_handle.add_attr("ballTwist", at="float", k=True)
        self.toe_twist = self.ik_handle.add_attr("toeTwist", at="float", k=True)
        self.ball_roll_compensate = self.ik_handle.add_attr("ballRollCompensate", at="float", k=False, dv=5)
        self.tip_start_rise = self.ik_handle.add_attr("tipStartRise", at="float", k=False, dv=30)
        self.tip_end_rise = self.ik_handle.add_attr("tipEndRise", at="float", k=False, dv=60)
        self.soft_radius = self.ik_handle.add_attr("softRadius", at="float", k=False, dv=0.4)
        self.add_module(self.ik_handle)

        self.ik_spsw.switch_int.connect(self.ik_spsw_attr)

        self.foot_roll = FootRoll(self.name.replace(extra="roll"))
        self.foot_roll.external_structure = self.structure.structure
        self.foot_roll.bank_in_index = "bankIn"
        self.foot_roll.bank_out_index = "bankOut"
        self.foot_roll.heel_index = "heel"
        self.foot_roll.tip_index = "tip"
        self.foot_roll.bank_ball_index = "ballBank"
        self.foot_roll.in_roll_flt.connect(self.roll_attr)
        self.foot_roll.indices = self.INDICES[2:]
        self.foot_roll.in_parent_mtx.connect(self.ik_handle.out_normalized_mtx)
        self.foot_roll.in_bank_flt.connect(self.bank_attr)
        self.foot_roll.in_ball_roll_compensate.connect(self.ball_roll_compensate)
        self.foot_roll.in_tip_start_rise.connect(self.tip_start_rise)
        self.foot_roll.in_tip_end_rise.connect(self.tip_end_rise)
        self.foot_roll.in_heel_twist.connect(self.heel_twist)
        self.foot_roll.in_ball_twist.connect(self.ball_twist)
        self.foot_roll.in_toe_twist.connect(self.toe_twist)
        self.add_module(self.foot_roll)

        self.pole_offset = PoleVectorOffsetSystem(self.name)
        self.pole_offset.distance = 10.0
        self.pole_offset.start_index = self.INDICES[0]
        self.pole_offset.pole_index = self.INDICES[1]
        self.pole_offset.end_index = self.INDICES[2]

        self.ik_pole = control.ControlGenerator(self.name.replace(extra="ik", index="pole"))
        self.ik_pole.in_parent_mtx.connect(self.in_global)
        self.ik_pole.in_visibility.connect(self.ik_vis.out_flt)
        self.ik_pole.external_structure = self.structure.structure
        self.ik_pole.index = self.INDICES[1]
        self.ik_pole.set_offset_system(self.pole_offset)
        self.ik_pole.default_shape = shape.ShapeData(
            points=shape.scale(shape.CUBE, [2, 2, 2]),
            color=self.color,
            degree=1
        )
        self.ik_pole.remove_attr(*constants.ATTR_R, *constants.ATTR_S)
        self.add_module(self.ik_pole)

        ik_stretch = ik.Stretch(self.name.replace(extra="ikStretch"))
        ik_stretch.indices = self.INDICES[:3]
        ik_stretch.external_structure = self.structure.structure
        ik_stretch.in_start_mtx.connect(self.in_parent)
        ik_stretch.in_inv_scale_mtx.connect(self.in_localize)
        ik_stretch.in_end_mtx.connect(self.foot_roll.out_normalized_mtxs, src_index=0)
        ik_stretch.in_custom_stretch.connect(self.upper_stretch, dst_index=0)
        ik_stretch.in_custom_stretch.connect(self.lower_stretch, dst_index=1)
        ik_stretch.in_soft_radius.connect(self.soft_radius)
        self.ik_stretch = self.add_module(ik_stretch)

        self.ik = ik.IK(self.name.replace(extra="ik"))
        self.ik.in_stretch_flt.connect(ik_stretch.out_length_flts)
        self.ik.in_pole_mtx.connect(self.ik_pole.out_world_mtx)
        self.ik.in_driver_mtx.connect(self.foot_roll.out_normalized_mtxs, src_index=0)
        self.ik.in_parent_mtx.connect(self.in_parent)
        self.ik.external_structure = self.structure.structure
        self.ik.indices = self.INDICES[:3]
        self.ik.pole_index = self.INDICES[1]
        self.add_module(self.ik)

        self.ik_line = Line(self.name.replace(extra="ikLine"))
        self.ik_line.external_structure = self.structure.structure
        self.ik_line.start_mtx.connect(self.ik_pole.out_world_mtx)
        self.ik_line.end_mtx.connect(self.ik.out_mtx, src_index=1)
        self.ik_line.in_visibility.connect(self.ik_vis.out_flt)
        self.add_module(self.ik_line)

        self.blend = MatricesSwitch(self.name.replace(extra="blend"))
        self.blend.in_a_mtxs.connect(self.fk.out_normalized_mtx)
        self.blend.in_b_mtxs.connect(self.ik.out_normalized_mtx, src_index=0, dst_index=0)
        self.blend.in_b_mtxs.connect(self.ik.out_normalized_mtx, src_index=1, dst_index=1)
        self.blend.in_b_mtxs.connect(self.foot_roll.out_normalized_mtxs, src_index=0, dst_index=2)
        self.blend.in_b_mtxs.connect(self.foot_roll.out_normalized_mtxs, src_index=1, dst_index=3)
        self.blend.in_b_mtxs.connect(self.foot_roll.out_normalized_mtxs, src_index=2, dst_index=4)
        self.blend.external_structure = self.structure.structure
        self.blend.in_switch_bool.connect(self.fk_ik_attr)
        self.add_module(self.blend)

        self.switch.in_parent_mtx.connect(self.blend.out_mtxs, src_index=2)

        self.localize_joints = MatricesMult(self.name.replace(extra="local"))
        self.localize_joints.external_structure = self.structure.structure
        self.localize_joints.in_mtxs.connect(self.blend.out_mtxs)
        self.localize_joints.in_parent_mtx.connect(self.in_localize)
        self.add_module(self.localize_joints)

        self.output_joints = JointRenderer(self.name.replace(extra="skin"))
        self.output_joints.indices = self.INDICES
        self.output_joints.nice_name = self.name
        self.output_joints.external_structure = self.structure.structure
        self.output_joints.in_mtxs.connect(self.localize_joints.out_mtxs)
        self.output_joints.for_skinning = True
        self.add_module(self.output_joints)

        # twist
        upper_twist = Piston(self.name.replace(extra="upperTwist"))
        upper_twist.indices = self.INDICES[:2]
        upper_twist.external_structure = self.structure.structure
        upper_twist.in_start_mtx.connect(self.in_local_parent)
        upper_twist.in_end_mtx.connect(self.localize_joints.out_mtxs, src_index=1)
        self.upper_twist = self.add_module(upper_twist)

        upper_twist_joints = JointRenderer(self.name.replace(extra="upperTwistSkin"))
        upper_twist_joints.indices = range(upper_twist.sample_count)
        upper_twist_joints.nice_name = self.name.replace(extra="upperTwist")
        upper_twist_joints.external_structure = self.structure.structure
        upper_twist_joints.in_mtxs.connect(self.upper_twist.out_mtxs)
        upper_twist_joints.from_guides = False
        upper_twist_joints.for_skinning = True
        self.upper_twist_joints = self.add_module(upper_twist_joints)

        lower_twist = Piston(self.name.replace(extra="lowerTwist"))
        lower_twist.indices = self.INDICES[1:3]
        lower_twist.external_structure = self.structure.structure
        lower_twist.in_start_mtx.connect(self.localize_joints.out_mtxs, src_index=1)
        lower_twist.in_end_mtx.connect(self.localize_joints.out_mtxs, src_index=2)
        self.lower_twist = self.add_module(lower_twist)

        lower_twist_joints = JointRenderer(self.name.replace(extra="lowerTwistSkin"))
        lower_twist_joints.indices = range(lower_twist.sample_count)
        lower_twist_joints.nice_name = self.name.replace(extra="lowerTwist")
        lower_twist_joints.external_structure = self.structure.structure
        lower_twist_joints.in_mtxs.connect(self.lower_twist.out_mtxs)
        lower_twist_joints.from_guides = False
        lower_twist_joints.for_skinning = True
        self.lower_twist_joints = self.add_module(lower_twist_joints)

        for mod in self.modules[1:]:
            mod.external_structure = self.structure.structure



