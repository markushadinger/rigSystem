from src.architecture import builder

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
from src.components.ribbon import RibbonSkin

from src.components.matrixBlend import MatrixLocalBlend

from src.components import control, ik
from src.lib import constants

from src.lib.naming import Name
from src.rig.controls import shape


class BipedNeck(builder.Builder):
    INDICES = ["0", "end"]

    def __init__(self, name: Name):
        super().__init__(name)

        self.structure = Component(self.name)
        self.in_global = self.structure.add_deferred_plug(DeferredPlug("in_global", "input", MATRIX))
        self.in_localize = self.structure.add_deferred_plug(DeferredPlug("in_localize", "input", MATRIX))
        self.in_parent = self.structure.add_deferred_plug(DeferredPlug("in_parent", "input", MATRIX))
        self.in_local_parent = self.structure.add_deferred_plug(DeferredPlug("in_parent_local", "input", MATRIX))
        self.add_module(self.structure)

        self.neck_spsw = SpaceSwitch(self.name.replace(extra=f"{self.INDICES[0]}spsw"))
        self.neck_spsw.index = self.INDICES[0]
        self.neck_spsw.external_structure = self.structure.structure
        self.neck_spsw.parent_mtx.connect(self.in_parent)
        self.neck_spsw.rotation = True
        self.add_module(self.neck_spsw)

        self.neck_ctrl = control.ControlGenerator(self.name.replace(extra=self.INDICES[0]))
        self.neck_ctrl.index = self.INDICES[0]
        self.neck_ctrl.in_parent_mtx.connect(self.neck_spsw.out_mtx)
        self.neck_ctrl.external_structure = self.structure.structure
        self.neck_ctrl.default_shape = shape.ShapeData(
            points=shape.translate(shape.rotate(shape.scale(shape.CIRCLE, 12), [0, 0, 0]), [0, 5, 0]),
            color=shape.SIDE_COLOR[self.name.side],
            degree=1)
        self.neck_spsw_attr = self.neck_ctrl.add_attr("space", at="enum", k=True, dv=0, en="-")
        self.add_module(self.neck_ctrl)

        self.neck_spsw.switch_int.connect(self.neck_spsw_attr)

        # ----- head
        self.head_spsw = SpaceSwitch(self.name.replace(extra=f"{self.INDICES[-1]}SpSw"))
        self.head_spsw.index = self.INDICES[-1]
        self.head_spsw.external_structure = self.structure.structure
        self.head_spsw.parent_mtx.connect(self.neck_ctrl.out_normalized_mtx)
        self.head_spsw.rotation = True
        self.add_module(self.head_spsw)

        self.head_ctrl = control.ControlGenerator(self.name.replace(extra=self.INDICES[-1]))
        self.head_ctrl.index = self.INDICES[-1]
        self.head_ctrl.in_parent_mtx.connect(self.head_spsw.out_mtx)
        self.head_ctrl.external_structure = self.structure.structure
        self.head_ctrl.default_shape = shape.ShapeData(
            points=shape.translate(shape.rotate(shape.scale(shape.CUBE, 10), [0, 0, 0]), [0, 5, 0]),
            color=shape.SIDE_COLOR[self.name.side],
            degree=1)
        self.head_spsw_attr = self.head_ctrl.add_attr("space", at="enum", k=True, dv=0, en="-")
        self.neck_follow_head_attr = self.head_ctrl.add_attr("neck_follow", at="float", k=False, dv=0.2, min=0, max=1)
        self.add_module(self.head_ctrl)

        self.head_spsw.switch_int.connect(self.head_spsw_attr)

        # twist
        self.twist = Piston(self.name.replace(extra="upperTwist"))
        self.twist.indices = self.INDICES
        self.twist.sample_count = 3
        self.twist.aim_vector = "y"
        self.twist.up_vector = "x"
        self.twist.end_up_axis = "x"
        self.twist.start_up_axis = "x"
        self.twist.external_structure = self.structure.structure
        self.twist.in_start_mtx.connect(self.in_parent)
        self.twist.in_end_mtx.connect(self.head_ctrl.out_normalized_mtx)
        self.add_module(self.twist)

        self.head_blend = MatrixLocalBlend(self.name.replace(extra="headBlend"))
        self.head_blend.external_structure = self.structure.structure
        self.head_blend.in_mtx.connect(self.twist.out_mtxs, src_index=self.twist.sample_count - 1)
        self.head_blend.in_blend.connect(self.head_ctrl.out_world_mtx)
        self.head_blend.in_blend_rotate.connect(self.neck_follow_head_attr)
        self.add_module(self.head_blend)

        self.localize_twist = MatricesMult(self.name.replace(extra="local"))
        self.localize_twist.external_structure = self.structure.structure
        self.localize_twist.in_mtxs.connect(self.twist.out_mtxs, src_index=0, dst_index=0)
        self.localize_twist.in_mtxs.connect(self.head_blend.out_mtx, dst_index=1)
        self.localize_twist.in_parent_mtx.connect(self.in_localize)
        self.add_module(self.localize_twist)

        self.ribbon = RibbonSkin(self.name.replace(extra="ribbon"))
        self.ribbon.in_mtx.connect(self.localize_twist.out_mtxs)
        self.ribbon.external_structure = self.structure.structure
        self.ribbon.sample_points = 5
        self.ribbon.u_knot_count = 5
        self.ribbon.degree = 2
        self.add_module(self.ribbon)

        self.twist_joints = JointRenderer(self.name.replace(extra="twistSkin"))
        self.twist_joints.indices = range(self.ribbon.sample_points)
        self.twist_joints.nice_name = self.name.replace(extra="twist")
        self.twist_joints.external_structure = self.structure.structure
        self.twist_joints.in_mtxs.connect(self.ribbon.out_mtx)
        self.twist_joints.from_guides = False
        self.twist_joints.for_skinning = True
        self.add_module(self.twist_joints)

        self.localize_head = MatricesMult(self.name.replace(extra="local"))
        self.localize_head.external_structure = self.structure.structure
        self.localize_head.in_mtxs.connect(self.head_ctrl.out_world_mtx, dst_index=0)
        self.localize_head.in_parent_mtx.connect(self.in_localize)
        self.add_module(self.localize_head)

        self.head_joint = JointRenderer(self.name.replace(extra="headSkin"))
        self.head_joint.indices = self.INDICES[-1:]
        self.head_joint.nice_name = self.name.replace(extra=None)
        self.head_joint.external_structure = self.structure.structure
        self.head_joint.in_mtxs.connect(self.localize_head.out_mtxs)
        self.head_joint.from_guides = False
        self.head_joint.for_skinning = True
        self.add_module(self.head_joint)
