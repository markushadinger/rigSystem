from src.architecture import builder

from src.components.offset_systems.poleVectorOffsetSystem import PoleVectorOffsetSystem

from src.components.matricesSwitch import MatricesSwitch
from src.components.jointRenderer import JointRenderer
from src.assembly.basic.fk_chain import FkChain
from src.components._comp_base import Component
from src.components.matrixBlend import MatrixNormalBlend
from src.components.aim import Aim
from src.components.matricesMult import MatricesMult
from src.components.piston import Piston
from src.components.mathFloat import OneMinus
from src.rig.module.deferred_plug import DeferredPlug, MATRIX,FLOAT

from src.components import control, ik
from src.lib import constants

from src.lib.naming import Name
from src.rig.controls import shape


class BipedFinger(builder.Builder):
    INDICES = [0, 1, 2, 3]
    METACARPAL_INDEX = "meta"

    def __init__(self, name: Name, has_metacarpal: bool):
        super().__init__(name)

        self.has_metacarpal: bool = has_metacarpal

        self.color = shape.SIDE_COLOR[self.name.side]
        self.ik_shape = shape.ShapeData(
            points=shape.scale(shape.CUBE, 5),
            color=self.color,
            degree=1)

        self.switch_shape = shape.ShapeData(
            points=shape.translate(shape.scale(shape.DROPLET, [3, 3, -3]), [0, 0, 10]),
            color=self.color,
            degree=1)

        self.structure = Component(self.name)
        self.in_global = self.structure.add_deferred_plug(DeferredPlug("in_global", "input", MATRIX))
        self.in_localize = self.structure.add_deferred_plug(DeferredPlug("in_localize", "input", MATRIX))
        self.in_parent = self.structure.add_deferred_plug(DeferredPlug("in_parent", "input", MATRIX))
        self.fk_ik_attr = self.structure.add_deferred_plug(DeferredPlug("in_fk_ik", "input", FLOAT))
        self.add_module(self.structure)

        self.fk_vis_invert = OneMinus(self.name.replace(extra="fkVisInvert"))
        self.fk_vis_invert.external_structure = self.structure.structure
        self.fk_vis_invert.in_flt.connect(self.fk_ik_attr)
        self.add_module(self.fk_vis_invert)

        self.fk = FkChain(self.name.replace(extra="fk"))
        self.fk.in_mtx.connect(self.in_parent)
        self.fk.in_visibility.connect(self.fk_vis_invert.out_flt)
        self.fk.indices = self.INDICES[:-1]
        self.fk.structure.external_structure = self.structure.structure
        self.fk.default_shape = shape.ShapeData(
            points=shape.rotate(shape.scale(shape.CIRCLE, 2), [0, 0, 90]),
            color=self.color,
            degree=1)
        self.fk.for_skinning = True
        self.fk.init_submodules()
        self.add_module(self.fk)

        self.ik_ctrl = control.ControlGenerator(self.name.replace(extra="ik", index=self.INDICES[-1]))
        self.ik_ctrl.in_visibility.connect(self.fk_ik_attr)
        self.ik_ctrl.in_parent_mtx.connect(self.in_parent)
        self.ik_ctrl.index = self.INDICES[-1]
        self.ik_ctrl.external_structure = self.structure.structure
        self.ik_ctrl.default_shape = shape.ShapeData(
            points=shape.scale(shape.CUBE, 1),
            color=self.color,
            degree=1
        )
        self.ik_ctrl.remove_attr(*constants.ATTR_S)
        self.ik_tip_aut_follow = self.ik_ctrl.add_attr("followTip", at="float", min=0, max=1, k=True, dv=1)
        self.add_module(self.ik_ctrl)

        self.pole_offset = PoleVectorOffsetSystem(self.name)
        self.pole_offset.distance = 10.0
        self.pole_offset.start_index = self.INDICES[0]
        self.pole_offset.pole_index = self.INDICES[1]
        self.pole_offset.end_index = self.INDICES[2]

        self.ik_pole = control.ControlGenerator(self.name.replace(extra="ik", index="pole"))
        self.ik_pole.in_parent_mtx.connect(self.ik_ctrl.out_normalized_mtx)
        self.ik_pole.external_structure = self.structure.structure
        self.ik_pole.index = self.INDICES[1]
        self.ik_pole.set_offset_system(self.pole_offset)
        self.ik_pole.has_shape = False
        self.add_module(self.ik_pole)

        ik_full_stretch = ik.Stretch(self.name.replace(extra="ikFullStretch"))
        ik_full_stretch.in_custom_stretch.default_value = 1
        ik_full_stretch.enable_soft_ik = False
        ik_full_stretch.indices = self.INDICES
        ik_full_stretch.external_structure = self.structure.structure
        ik_full_stretch.in_start_mtx.connect(self.in_parent)
        ik_full_stretch.in_inv_scale_mtx.connect(self.in_localize)
        ik_full_stretch.in_end_mtx.connect(self.ik_ctrl.out_normalized_mtx)
        ik_full_stretch.in_soft_radius.default_value = 0.01
        self.ik_stretch = self.add_module(ik_full_stretch)

        self.ik_full = ik.IK(self.name.replace(extra="ikFull"))
        self.ik_full.in_pole_mtx.connect(self.ik_pole.out_world_mtx)
        self.ik_full.in_driver_mtx.connect(self.ik_ctrl.out_normalized_mtx)
        self.ik_full.in_parent_mtx.connect(self.in_parent)
        self.ik_full.in_stretch_flt.connect(ik_full_stretch.out_length_flts)
        self.ik_full.external_structure = self.structure.structure
        self.ik_full.indices = self.INDICES
        self.ik_full.pole_index = self.INDICES[1]
        self.add_module(self.ik_full)

        tip_ik_mtx_blend = MatrixNormalBlend(self.name.replace(extra="ikTipBlend"))
        tip_ik_mtx_blend.external_structure = self.structure.structure
        tip_ik_mtx_blend.index = self.INDICES[-1]
        tip_ik_mtx_blend.in_mtx.connect(self.ik_full.out_normalized_mtx, src_index=3)
        tip_ik_mtx_blend.in_blend.connect(self.ik_ctrl.out_normalized_mtx)
        tip_ik_mtx_blend.in_blend_rotate.connect(self.ik_tip_aut_follow)
        self.add_module(tip_ik_mtx_blend)

        ik_tip_stretch = ik.Stretch(self.name.replace(extra="ikTipStretch"))
        ik_tip_stretch.in_custom_stretch.default_value = 1
        ik_tip_stretch.enable_soft_ik = False
        ik_tip_stretch.indices = self.INDICES[:3]
        ik_tip_stretch.external_structure = self.structure.structure
        ik_tip_stretch.in_start_mtx.connect(self.in_parent)
        ik_tip_stretch.in_inv_scale_mtx.connect(self.in_localize)
        ik_tip_stretch.in_end_mtx.connect(tip_ik_mtx_blend.out_mtx)
        ik_tip_stretch.in_soft_radius.default_value = 0.01
        self.ik_stretch = self.add_module(ik_tip_stretch)

        self.ik_tip = ik.IK(self.name.replace(extra="ikTip"))
        self.ik_tip.in_stretch_flt.connect(ik_tip_stretch.out_length_flts)
        self.ik_tip.in_pole_mtx.connect(self.ik_pole.out_world_mtx)
        self.ik_tip.in_driver_mtx.connect(tip_ik_mtx_blend.out_mtx)
        self.ik_tip.in_parent_mtx.connect(self.in_parent)
        self.ik_tip.external_structure = self.structure.structure
        self.ik_tip.indices = self.INDICES[:-1]
        self.ik_tip.pole_index = self.INDICES[1]
        self.add_module(self.ik_tip)

        self.aim = Aim(self.name.replace(extra="ikTipAim"))
        self.aim.external_structure = self.structure.structure
        self.aim.in_mtx.connect(self.ik_tip.out_mtx, src_index=2)
        self.aim.target_mtx.connect(self.ik_ctrl.out_world_mtx)
        self.aim.up_mtx.connect(self.ik_ctrl.out_world_mtx)
        self.add_module(self.aim)

        if self.has_metacarpal:
            self.metacarpal_ctrl = control.ControlGenerator(self.name.replace(extra="meta"))
            self.metacarpal_ctrl.in_parent_mtx.connect(self.in_parent)
            self.metacarpal_ctrl.index = self.INDICES[0]
            self.metacarpal_ctrl.external_structure = self.structure.structure
            self.metacarpal_ctrl.default_shape = shape.ShapeData(
                points=shape.translate(shape.rotate(shape.scale(shape.TRIANGLE, 0.75), (-90, 90, 0)), (0, -2.5, 0)),
                color=self.color,
                degree=1
            )
            self.metacarpal_ctrl.remove_attr(*constants.ATTR_R, *constants.ATTR_S)
            self.add_module(self.metacarpal_ctrl)

            self.meta_carpal = Piston(self.name.replace(extra="metaTwist"))
            self.meta_carpal.indices = self.METACARPAL_INDEX, self.INDICES[0]
            self.meta_carpal.sample_count = 2
            self.meta_carpal.external_structure = self.structure.structure
            self.meta_carpal.in_start_mtx.connect(self.in_parent)
            self.meta_carpal.in_end_mtx.connect(self.metacarpal_ctrl.out_normalized_mtx)
            self.add_module(self.meta_carpal)

            metacarpal_blend = MatrixNormalBlend(self.name.replace(extra="metaBlend"))
            metacarpal_blend.external_structure = self.structure.structure
            metacarpal_blend.index = self.INDICES[0]
            metacarpal_blend.in_mtx.connect(self.in_parent)
            metacarpal_blend.in_blend.connect(self.meta_carpal.out_norm_mtxs, src_index=1)
            metacarpal_blend.in_blend_translate.default_value = 1
            self.add_module(metacarpal_blend)

            self.fk.in_mtx.connect(metacarpal_blend.out_mtx)
            self.ik_full.in_parent_mtx.connect(metacarpal_blend.out_mtx)
            self.ik_tip.in_parent_mtx.connect(metacarpal_blend.out_mtx)
            ik_full_stretch.in_start_mtx.connect(metacarpal_blend.out_mtx)
            ik_tip_stretch.in_start_mtx.connect(metacarpal_blend.out_mtx)

        self.blend = MatricesSwitch(self.name.replace(extra="blend"))
        self.blend.in_a_mtxs.connect(self.fk.out_mtx)
        self.blend.in_b_mtxs.connect(self.ik_tip.out_mtx, src_index=0, dst_index=0)
        self.blend.in_b_mtxs.connect(self.ik_tip.out_mtx, src_index=1, dst_index=1)
        self.blend.in_b_mtxs.connect(self.aim.out_mtx, dst_index=2)
        self.blend.external_structure = self.structure.structure
        self.blend.in_switch_bool.connect(self.fk_ik_attr)
        self.add_module(self.blend)

        self.localize_joints = MatricesMult(self.name.replace(extra="local"))
        self.localize_joints.external_structure = self.structure.structure

        self.localize_joints.in_mtxs.connect(self.blend.out_mtxs, src_index=0, dst_index=0)
        self.localize_joints.in_mtxs.connect(self.blend.out_mtxs, src_index=1, dst_index=1)
        self.localize_joints.in_mtxs.connect(self.blend.out_mtxs, src_index=2, dst_index=2)

        if self.has_metacarpal:
            self.localize_joints.in_mtxs.connect(self.meta_carpal.out_mtxs, src_index=0, dst_index=3)

        self.localize_joints.in_parent_mtx.connect(self.in_localize)
        self.add_module(self.localize_joints)

        self.output_joints = JointRenderer(self.name.replace(extra="skin"))
        self.output_joints.indices = self.INDICES[:-1] + ([self.METACARPAL_INDEX] if self.has_metacarpal else [])
        self.output_joints.nice_name = self.name
        self.output_joints.external_structure = self.structure.structure
        self.output_joints.in_mtxs.connect(self.localize_joints.out_mtxs)
        self.output_joints.for_skinning = True
        self.output_joints.from_guides = False
        self.add_module(self.output_joints)

        # self.fk_spsw_attr = self.fk.fk_modules[0].add_attr("space", at="enum", k=True, dv=0, en="-")
        # self.fk_spsw.switch_int.connect(self.fk_spsw_attr)
        #
        # # --- ik
        #
        # self.ik_spsw = SpaceSwitch(self.name.replace(extra="ikSpSw"))
        # self.ik_spsw.parent_mtx.connect(self.in_global)
        # self.ik_spsw.index = self.INDICES[2]
        # self.ik_spsw.rotation = True
        # self.ik_spsw.translation = True
        # self.add_module(self.ik_spsw)
        #
        # self.ik_handle = control.ControlGenerator(self.name.replace(extra="ik", index=self.INDICES[2]))
        # self.ik_handle.in_parent_mtx.connect(self.ik_spsw.out_mtx)
        # self.ik_handle.in_visibility.connect(self.ik_vis.out_flt)
        # self.ik_handle.index = self.INDICES[2]
        # self.ik_handle.external_structure = self.structure.structure
        # self.ik_handle.default_shape = shape.ShapeData(
        #     points=shape.scale(shape.CUBE, 5),
        #     color=self.color,
        #     degree=1
        # )
        # self.ik_spsw_attr = self.ik_handle.add_attr("space", at="enum", k=True, dv=0, en="-")
        # self.ik_handle.add_seperator("Stretch")
        # self.upper_stretch = self.ik_handle.add_attr("upperStretch", at="float", k=True, dv=1, min=0.01)
        # self.lower_stretch = self.ik_handle.add_attr("lowerStretch", at="float", k=True, dv=1, min=0.01)
        # self.ik_handle.add_seperator("Roll")
        # self.roll_attr = self.ik_handle.add_attr("roll", at="float", k=True)
        # self.bank_attr = self.ik_handle.add_attr("bank", at="float", k=True)
        # self.ik_handle.add_seperator("Twist")
        # self.heel_twist = self.ik_handle.add_attr("heelTwist", at="float", k=True)
        # self.ball_twist = self.ik_handle.add_attr("ballTwist", at="float", k=True)
        # self.toe_twist = self.ik_handle.add_attr("toeTwist", at="float", k=True)
        # self.ball_roll_compensate = self.ik_handle.add_attr("ballRollCompensate", at="float", k=False, dv=5)
        # self.tip_start_rise = self.ik_handle.add_attr("tipStartRise", at="float", k=False, dv=30)
        # self.tip_end_rise = self.ik_handle.add_attr("tipEndRise", at="float", k=False, dv=60)
        # self.soft_radius = self.ik_handle.add_attr("softRadius", at="float", k=False, dv=0.4)
        # self.add_module(self.ik_handle)
        #
        # self.ik_spsw.switch_int.connect(self.ik_spsw_attr)
        #
        # self.pole_offset = PoleVectorOffsetSystem(self.name)
        # self.pole_offset.distance = 10.0
        # self.pole_offset.start_index = self.INDICES[0]
        # self.pole_offset.pole_index = self.INDICES[1]
        # self.pole_offset.end_index = self.INDICES[2]
        #
        # self.ik_pole = control.ControlGenerator(self.name.replace(extra="ik", index="pole"))
        # self.ik_pole.in_parent_mtx.connect(self.in_global)
        # self.ik_pole.in_visibility.connect(self.ik_vis.out_flt)
        # self.ik_pole.external_structure = self.structure.structure
        # self.ik_pole.index = self.INDICES[1]
        # self.ik_pole.set_offset_system(self.pole_offset)
        # self.ik_pole.default_shape = shape.ShapeData(
        #     points=shape.scale(shape.translate(shape.PYRAMID, [0, -1, 0]), [2, -2, 2]),
        #     color=self.color,
        #     degree=1
        # )
        # for attr in "rs":
        #     for axis in "xyz":
        #         self.ik_pole.remove_attr(attr + axis)
        # self.add_module(self.ik_pole)
        #
        # ik_stretch = ik.Stretch(self.name.replace(extra="ikStretch"))
        # ik_stretch.indices = self.INDICES[:3]
        # ik_stretch.external_structure = self.structure.structure
        # ik_stretch.in_start_mtx.connect(self.in_parent)
        # ik_stretch.in_inv_scale_mtx.connect(self.in_localize)
        # ik_stretch.in_end_mtx.connect(self.foot_roll.out_normalized_mtxs, src_index=0)
        # ik_stretch.in_custom_stretch.connect(self.upper_stretch, dst_index=0)
        # ik_stretch.in_custom_stretch.connect(self.lower_stretch, dst_index=1)
        # ik_stretch.in_soft_radius.connect(self.soft_radius)
        # self.ik_stretch = self.add_module(ik_stretch)
        #
        # self.ik = ik.IK(self.name.replace(extra="ik"))
        # self.ik.in_stretch_flt.connect(ik_stretch.out_length_flts)
        # self.ik.in_pole_mtx.connect(self.ik_pole.out_world_mtx)
        # self.ik.in_driver_mtx.connect(self.foot_roll.out_normalized_mtxs, src_index=0)
        # self.ik.in_parent_mtx.connect(self.in_parent)
        # self.ik.external_structure = self.structure.structure
        # self.ik.indices = self.INDICES[:3]
        # self.ik.pole_index = self.INDICES[1]
        # self.add_module(self.ik)
        #
        # self.ik_line = Line(self.name.replace(extra="ikLine"))
        # self.ik_line.external_structure = self.structure.structure
        # self.ik_line.start_mtx.connect(self.ik_pole.out_world_mtx)
        # self.ik_line.end_mtx.connect(self.ik.out_mtx, src_index=1)
        # self.ik_line.in_visibility.connect(self.ik_vis.out_flt)
        # self.add_module(self.ik_line)
        #
        # self.blend = MatricesSwitch(self.name.replace(extra="blend"))
        # self.blend.in_a_mtxs.connect(self.fk.out_normalized_mtx)
        # self.blend.in_b_mtxs.connect(self.ik.out_normalized_mtx, src_index=0, dst_index=0)
        # self.blend.in_b_mtxs.connect(self.ik.out_normalized_mtx, src_index=1, dst_index=1)
        # self.blend.in_b_mtxs.connect(self.foot_roll.out_normalized_mtxs, src_index=0, dst_index=2)
        # self.blend.in_b_mtxs.connect(self.foot_roll.out_normalized_mtxs, src_index=1, dst_index=3)
        # self.blend.in_b_mtxs.connect(self.foot_roll.out_normalized_mtxs, src_index=2, dst_index=4)
        # self.blend.external_structure = self.structure.structure
        # self.blend.in_switch_bool.connect(self.fk_ik_attr)
        # self.add_module(self.blend)
        #
        # self.switch.in_parent_mtx.connect(self.blend.out_mtxs, src_index=2)
        #
        # self.localize_joints = MatricesMult(self.name.replace(extra="local"))
        # self.localize_joints.external_structure = self.structure.structure
        # self.localize_joints.in_mtxs.connect(self.blend.out_mtxs)
        # self.localize_joints.in_parent_mtx.connect(self.in_localize)
        # self.add_module(self.localize_joints)
        #
        # self.output_joints = JointRenderer(self.name.replace(extra="skin"))
        # self.output_joints.indices = self.INDICES
        # self.output_joints.nice_name = self.name
        # self.output_joints.external_structure = self.structure.structure
        # self.output_joints.in_mtxs.connect(self.localize_joints.out_mtxs)
        # self.output_joints.for_skinning = True
        # self.add_module(self.output_joints)
        #
        # # twist
        # upper_twist = Piston(self.name.replace(extra="upperTwist"))
        # upper_twist.indices = self.INDICES[:2]
        # upper_twist.external_structure = self.structure.structure
        # upper_twist.in_start_mtx.connect(self.in_local_parent)
        # upper_twist.in_end_mtx.connect(self.localize_joints.out_mtxs, src_index=1)
        # self.upper_twist = self.add_module(upper_twist)
        #
        # upper_twist_joints = JointRenderer(self.name.replace(extra="upperTwistSkin"))
        # upper_twist_joints.indices = range(upper_twist.sample_count)
        # upper_twist_joints.nice_name = self.name.replace(extra="upperTwist")
        # upper_twist_joints.external_structure = self.structure.structure
        # upper_twist_joints.in_mtxs.connect(self.upper_twist.out_mtxs)
        # upper_twist_joints.from_guides = False
        # upper_twist_joints.for_skinning = True
        # self.upper_twist_joints = self.add_module(upper_twist_joints)
        #
        # lower_twist = Piston(self.name.replace(extra="lowerTwist"))
        # lower_twist.indices = self.INDICES[1:3]
        # lower_twist.external_structure = self.structure.structure
        # lower_twist.in_start_mtx.connect(self.localize_joints.out_mtxs, src_index=1)
        # lower_twist.in_end_mtx.connect(self.localize_joints.out_mtxs, src_index=2)
        # self.lower_twist = self.add_module(lower_twist)
        #
        # lower_twist_joints = JointRenderer(self.name.replace(extra="lowerTwistSkin"))
        # lower_twist_joints.indices = range(lower_twist.sample_count)
        # lower_twist_joints.nice_name = self.name.replace(extra="lowerTwist")
        # lower_twist_joints.external_structure = self.structure.structure
        # lower_twist_joints.in_mtxs.connect(self.lower_twist.out_mtxs)
        # lower_twist_joints.from_guides = False
        # lower_twist_joints.for_skinning = True
        # self.lower_twist_joints = self.add_module(lower_twist_joints)
        #
        # for mod in self.modules[1:]:
        #     mod.external_structure = self.structure.structure
