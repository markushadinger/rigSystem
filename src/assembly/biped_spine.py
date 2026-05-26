from src.architecture import builder

from src.components.jointRenderer import JointRenderer
from src.assembly.basic.fk_chain import FkChain
from src.components._comp_base import Component
from src.components.matricesMult import MatricesMult
from src.components.ribbon import Ribbon
from src.rig.module.deferred_plug import DeferredPlug, MATRIX

from src.lib.naming import Name
from src.rig.controls import shape


class BipedSpine(builder.Builder):

    def __init__(self, name: Name):
        super().__init__(name)

        self.color = shape.SIDE_COLOR[self.name.side]
        self.spine_shape = shape.ShapeData(points=shape.scale(shape.CIRCLE, 15), color=self.color, degree=1)
        self.hip_shape = shape.ShapeData(points=shape.scale(shape.CIRCLE, 15), color=shape.COLOR_GREEN, degree=1)

        self.hip_indices = ["hip0", "hip1"]
        self.spine_indices = list(range(4))

        self.color = shape.SIDE_COLOR[self.name.side]
        self.ik_shape = shape.ShapeData(points=shape.scale(shape.CUBE, 5), color=self.color, degree=1)

        self.structure = Component(self.name)
        self.in_global = self.structure.add_deferred_plug(DeferredPlug("in_global", "input", MATRIX))
        self.in_localize = self.structure.add_deferred_plug(DeferredPlug("in_localize", "input", MATRIX))
        self.in_parent = self.structure.add_deferred_plug(DeferredPlug("in_parent", "input", MATRIX))

        self.out_start = self.structure.add_deferred_plug(DeferredPlug("out_start", "input", MATRIX))
        self.out_end = self.structure.add_deferred_plug(DeferredPlug("out_end", "input", MATRIX))
        self.out_local_start = self.structure.add_deferred_plug(DeferredPlug("out_local_start", "input", MATRIX))
        self.out_local_end = self.structure.add_deferred_plug(DeferredPlug("out_local_end", "input", MATRIX))
        self.out_mtxs = self.structure.add_deferred_plug(DeferredPlug("out_mtxs", "input", MATRIX, multi=True))
        self.add_module(self.structure)

        # self.switch = control.ControlGenerator(self.name.replace(extra="switch"))
        # self.switch.index = self.INDICES[-1]
        # self.switch.external_structure = self.structure.structure
        # fk_ik_plug = self.switch.add_attr("fk_ik", dict(at="short", min=0, max=1, k=True))
        # self.add_module(self.switch)

        self.fk = FkChain(self.name.replace(extra="fk"))
        self.fk.default_shape = self.spine_shape
        self.fk.in_mtx.connect(self.in_parent)
        self.fk.indices = self.spine_indices
        self.fk.indices_without_shape = self.spine_indices[-1:]
        self.fk.structure.external_structure = self.structure.structure
        self.fk.init_submodules()
        self.add_module(self.fk)

        self.hip_fk = FkChain(self.name.replace(extra="fk"))
        self.hip_fk.in_mtx.connect(self.in_parent)
        self.hip_fk.default_shape = self.hip_shape
        self.hip_fk.indices = self.hip_indices
        self.hip_fk.indices_without_shape = self.hip_indices[-1:]
        self.hip_fk.structure.external_structure = self.structure.structure
        self.hip_fk.init_submodules()
        self.add_module(self.hip_fk)

        self.localize_joints = MatricesMult(self.name.replace(extra="local"))
        self.localize_joints.external_structure = self.structure.structure
        for i, _ in enumerate(self.hip_indices):
            self.localize_joints.in_mtxs.connect(self.hip_fk.out_mtx, src_index=i, dst_index=len(self.hip_indices) - i)

        for i, _ in enumerate(self.spine_indices[1:], start=1):
            self.localize_joints.in_mtxs.connect(self.fk.out_mtx, src_index=i, dst_index=len(self.hip_indices) + i)
        self.localize_joints.in_parent_mtx.connect(self.in_localize)
        self.add_module(self.localize_joints)

        self.localize_controls = MatricesMult(self.name.replace(extra="localCtrl"))
        self.localize_controls.external_structure = self.structure.structure
        self.localize_controls.in_mtxs.connect(self.hip_fk.fk_modules[-1].out_normalized_mtx, dst_index=0)
        self.localize_controls.in_mtxs.connect(self.fk.fk_modules[-1].out_normalized_mtx, dst_index=1)
        self.localize_controls.in_parent_mtx.connect(self.in_localize)
        self.add_module(self.localize_controls)

        self.ribbon = Ribbon(self.name.replace(extra="ribbon"))
        self.ribbon.in_mtx.connect(self.localize_joints.out_mtxs)
        self.ribbon.external_structure = self.structure.structure
        self.ribbon.flip_indices = list(range(len(self.hip_indices)))
        self.ribbon.sample_points = 10
        self.ribbon.degree = 2
        self.add_module(self.ribbon)

        self.output_joints = JointRenderer(self.name.replace(extra="skin"))
        self.output_joints.indices = range(self.ribbon.sample_points)
        self.output_joints.nice_name = self.name
        self.output_joints.external_structure = self.structure.structure
        self.output_joints.in_mtxs.connect(self.ribbon.out_mtx)
        self.output_joints.for_skinning = True
        self.output_joints.from_guides = False
        self.add_module(self.output_joints)

        self.out_start.connect(self.hip_fk.out_normalized_mtx, src_index=1)
        self.out_end.connect(self.fk.out_normalized_mtx, src_index=len(self.spine_indices) - 1)
        self.out_local_start.connect(self.localize_controls.out_mtxs, src_index=0)
        self.out_local_end.connect(self.localize_controls.out_mtxs, src_index=1)
        self.out_mtxs.connect(self.ribbon.out_normalized_mtx)
