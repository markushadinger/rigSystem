from maya import cmds

from src.components._comp_base import MacroComponent
from src.rig.module.deferred_plug import MATRIX, MATRIX_LIST
from src.lib import guide
from src.rig.controls import control, shape
from src.lib import hierarchy
from src.lib import naming
from src.lib import joint
from src.lib.nodes import Node
from src.rig.stack import Stack, ZERO
from src.rig.snippets import fk, ik


class BipedLeg(MacroComponent):
    INPUTS = {
        "placer_ws": MATRIX,
        "parent_ws": MATRIX,
    }

    OUTPUTS = {
        "fk_ctrls_ws": MATRIX_LIST,
        "ik_ctrl_ws": MATRIX,
        "joints_ws": MATRIX_LIST,
    }

    def __init__(self, name: str, side: str):
        super().__init__(name, side)
        self.INDICES = ["leg", "knee", "ankle", "ball", "toe"]

        self.aim_axis: str = "x"
        self.up_axis: str = "z"
        self.pole_vector_distance: float = 10

        self.ik_ctrl: Node | None = None
        self.pole_ctrl: Node | None = None
        self.fk_ctrls: list[Node] = []
        self.ik_joints: list[Node] = []
        self.joints: list[Node] = []

    def prepare(self):
        super().prepare()
        self.outputs["fk_ctrls_ws"].length = 5
        self.outputs["joints_ws"].length = 5

    def build_guides(self):

        parent = self.structure.guides

        # Build spine joints
        for i in self.indices:
            jnt_node = guide.create_guide_joint(i)
            cmds.parent(jnt_node, parent)
            parent = jnt_node

        # assign guide data to joints
        guide_data_dict = {naming.get_name(n, suffix=guide.SUFFIX): m for n, m in self.guide_data.data.items()}
        hierarchy.match_nodes_to_matrices(guide_data_dict)

    def build(self):
        """
        Build the spine controls.
        :return:
        """

        self.build_fk()
        self.build_ik()
        self.build_foot_roll()
        self.build_blend()

    def build_fk(self):
        """
        Build the FK controls for the spine and hips.
        """

        shape_data = [self.shape_data.get(i, {}) for i in self.indices]

        fk_builder = fk.Chain()
        fk_builder.names = [i.replace(extra="fk") for i in self.indices]
        fk_builder.matrices = self.guide_matrices
        fk_builder.shape_data = shape_data
        fk_builder.parent_mtx_plug = self.inputs["parent_ws"].plug
        fk_builder.parent_node = self.structure.controls
        fk_builder.build()

        self.fk_ctrls = fk_builder.out_controls

        for i, ctrl in enumerate(self.fk_ctrls):
            self.outputs["fk_ctrls_ws"].plug[i].connect(control.get_normalized_matrix_output(ctrl))

    def build_ik(self):

        default_shape = {
            "points": shape.CUBE,
            "degree": 1,
            "color": shape.SIDE_COLOR.get(self.name.side, "m")
        }

        # ik ctrl
        ik_name = self.name.replace(extra="ik")
        ik_shape = self.shape_data.get(ik_name, default_shape)

        self.ik_ctrl = control.build(ik_name)
        control.add_shape_from_dict(self.ik_ctrl, ik_shape)

        ik_stack = Stack(self.ik_ctrl)
        ik_zero = ik_stack.add(ZERO)
        ik_zero.offsetParentMatrix.connect(self.inputs["placer_ws"].plug)
        cmds.xform(ik_zero, worldSpace=True, matrix=self.guide_matrices[2])
        cmds.parent(ik_zero, self.structure.controls)

        # pole ctrl
        pole_name = self.name.replace(extra="pole")
        pole_shape = self.shape_data.get(pole_name, default_shape)
        self.pole_ctrl = control.build(pole_name)
        control.add_shape_from_dict(self.pole_ctrl, pole_shape)

        pole_stack = Stack(self.pole_ctrl)
        pole_zero = pole_stack.add(ZERO)
        pole_zero.offsetParentMatrix.connect(self.inputs["placer_ws"].plug)
        cmds.xform(pole_zero, worldSpace=True, matrix=self.guide_matrices[1])
        cmds.parent(pole_zero, self.structure.controls)

        pole_mtx = ik.get_pole_vector_matrix(*self.guide_matrices[:3], self.pole_vector_distance)
        cmds.xform(pole_zero, worldSpace=True, matrix=pole_mtx)

        self.ik_joints = joint.create_chain(
            matrices=self.guide_matrices,
            name=self.name.replace(extra="ik", suffix="jnt"),
            skin_joint=False
        )
        cmds.parent(self.ik_joints[0], self.structure.logic)
        self.ik_joints[0].offsetParentMatrix.connect(self.inputs["parent_ws"].plug)

        ik_handle, pole_constraint = ik.build_pole_ik(
            name=self.name.replace(extra="ik"),
            chain=self.ik_joints[:3],
            driver_plug=self.ik_ctrl.worldMatrix[0],
            pole_plug=self.pole_ctrl.worldMatrix[0]
        )
        cmds.parent(ik_handle, self.structure.logic)
        cmds.parent(pole_constraint, self.structure.logic)

    def build_blend(self):

        matrix_plug_dict = {}

        for key, node_list in {"fk": self.fk_ctrls, "ik": self.ik_joints}.items():
            local_matrix_plugs = []
            parent: None | Node = None

            for i, node in enumerate(node_list):
                if parent is None:
                    local_matrix_plugs.append(node.worldMatrix[0])

                else:
                    mmlt = Node.create("multMatrix", self.name.replace(index=i, extra=key, suffix="mmlt"))
                    mmlt.matrixIn[0].connect(node.worldMatrix[0])
                    mmlt.matrixIn[1].connect(parent.worldInverseMatrix[0])
                    local_matrix_plugs.append(mmlt.matrixSum)

                parent = node

            matrix_plug_dict[key] = local_matrix_plugs

        self.joints = joint.create_chain(
            matrices=[guide.DEFAULT_VALUE for i in self.indices],
            name=self.name.replace(suffix="jnt"),
            skin_joint=True
        )
        cmds.parent(self.joints[0], self.structure.deform)

        for i, (fk_plug, ik_plug, jnt) in enumerate(zip(matrix_plug_dict["fk"], matrix_plug_dict["ik"], self.joints)):
            blend = Node.create("blendMatrix", self.name.replace(index=i, suffix="blend"))
            blend.inputMatrix.connect(fk_plug)
            blend.target[0].targetMatrix.connect(ik_plug)
            jnt.offsetParentMatrix.connect(blend.outputMatrix)

    def build_foot_roll(self):
        self.ik_ctrl.add_attr("roll", at="float", k=True)
        self.ik_ctrl.add_attr("bank", at="float", k=True)
