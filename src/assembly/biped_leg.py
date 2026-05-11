from src.architecture import builder

from src.components.offset_systems.poleVectorOffsetSystem import PoleVectorOffsetSystem

from src.components.matricesSwitch import MatricesSwitch
from src.components.jointRenderer import JointRenderer
from src.assembly.basic.fk_chain import FkChain
from src.components._comp_base import Component
from src.components.matricesMult import MatricesMult
from src.rig.module.deferred_plug import DeferredPlug, MATRIX

from src.components import control, ik

from src.lib.naming import Name
from src.rig.controls import shape


class BipedLeg(builder.Builder):
    INDICES = ["leg", "knee", "ankle", "ball", "toe"]

    def __init__(self, name: Name):
        super().__init__(name)

        self.color = shape.SIDE_COLOR[self.name.side]
        self.ik_shape = shape.ShapeData(points=shape.scale(shape.CUBE, 5), color=self.color, degree=1)

        self.structure = Component(self.name)
        self.in_global = self.structure.add_deferred_plug(DeferredPlug("in_global", "input", MATRIX))
        self.in_localize = self.structure.add_deferred_plug(DeferredPlug("in_localize", "input", MATRIX))
        self.in_parent = self.structure.add_deferred_plug(DeferredPlug("in_parent", "input", MATRIX))
        self.add_module(self.structure)

        self.switch = control.ControlGenerator(self.name.replace(extra="switch"))
        self.switch.index = self.INDICES[2]
        self.switch.external_structure = self.structure.structure
        fk_ik_plug = self.switch.add_attr("fk_ik", dict(at="short", min=0, max=1, k=True))
        self.add_module(self.switch)

        self.fk = FkChain(self.name.replace(extra="fk"))
        self.fk.in_mtx.connect(self.in_parent)
        self.fk.indices = self.INDICES
        self.fk.structure.external_structure = self.structure.structure
        self.fk.for_skinning = True
        self.fk.init_submodules()
        self.add_module(self.fk)

        self.ik_handle = control.ControlGenerator(self.name.replace(extra="ik", index=self.INDICES[-1]))
        self.ik_handle.in_parent_mtx.connect(self.in_global)
        self.ik_handle.index = self.INDICES[2]
        self.ik_handle.external_structure = self.structure.structure
        self.ik_handle.default_shape = shape.ShapeData(
            points=shape.scale(shape.CUBE, 5),
            color=self.color,
            degree=1
        )
        self.add_module(self.ik_handle)

        self.pole_offset = PoleVectorOffsetSystem(self.name)
        self.pole_offset.distance = 10.0
        self.pole_offset.start_index = self.INDICES[0]
        self.pole_offset.pole_index = self.INDICES[1]
        self.pole_offset.end_index = self.INDICES[2]

        self.ik_pole = control.ControlGenerator(self.name.replace(extra="ik", index="pole"))
        self.ik_pole.in_parent_mtx.connect(self.in_global)
        self.ik_pole.external_structure = self.structure.structure
        self.ik_pole.index = self.INDICES[1]
        self.ik_pole.set_offset_system(self.pole_offset)
        self.ik_pole.default_shape = shape.ShapeData(
            points=shape.scale(shape.translate(shape.PYRAMID, [0, -1, 0]), [2, -2, 2]),
            color=self.color,
            degree=1
        )
        self.add_module(self.ik_pole)

        self.ik = ik.IK(self.name.replace(extra="ik"))
        self.ik.in_pole_mtx.connect(self.ik_pole.out_normalized_mtx)
        self.ik.in_driver_mtx.connect(self.ik_handle.out_normalized_mtx)
        self.ik.in_parent_mtx.connect(self.in_parent)
        self.ik.external_structure = self.structure.structure
        self.ik.indices = self.INDICES[:3]
        self.ik.pole_index = self.INDICES[1]
        self.add_module(self.ik)

        self.blend = MatricesSwitch(self.name.replace(extra="blend"))
        self.blend.in_a_mtxs.connect(self.ik.out_normalized_mtx)
        self.blend.in_b_mtxs.connect(self.fk.out_normalized_mtx)
        self.blend.external_structure = self.structure.structure
        self.blend.in_switch_bool.connect(fk_ik_plug)
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
