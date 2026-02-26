from src.components._comp_base import Component
from src.rig.data_manager import JsonDataManager
from src.rig.module.deferred_plug import TYPE_MATRIX, TYPE_MATRIX_LIST
from src.lib import guide
from src.rig.controls import control
from src.lib import hierarchy
from src.lib import naming
from src.lib import joint
from src.lib.nodes import Node

from src.rig.snippets import fk, curve, surface, pins

from maya import cmds
from maya.api import OpenMaya


class BpLimb(Component):
    INPUTS = {
        "parent_ws": TYPE_MATRIX,
    }

    OUTPUTS = {
        "fk_ctrls_ws": TYPE_MATRIX_LIST,
        "ik_ctrl_ws": TYPE_MATRIX,
        "joints_ws": TYPE_MATRIX_LIST,
    }

    def __init__(self, name):
        super().__init__(name)

        self.control_count: int = 5
        self.joint_count: int = 10
        self.aim_axis = "y"
        self.up_axis = "z"

        self.guide_version: int = -1
        self.guide_data: JsonDataManager | None = None
        self.shape_data: JsonDataManager | None = None

        self.ik_ctrls: list[Node] = []
        self.fk_ctrls: list[Node] = []
        self.joints: list[Node] = []

    def get_indices(self) -> list[str]:
        """
        Get the indices of the spine joints. The spine joints are named in the format {name}_{side}_{index}_guide.
        :return: A list of spine joint indices.
        """
        return [naming.get_name(self.name, index=i) for i in range(3)]

    def prepare(self):
        super().prepare()

        self.outputs["fk_ctrls_ws"].length = 3
        self.outputs["joints_ws"].length = 3

        self.guide_data = JsonDataManager(self.context.guide_file_path(self.name), self.guide_version)
        self.shape_data = JsonDataManager(self.context.shapes_file_path(self.name), -1)

    def load_guide_data(self):
        self.guide_data.load_if_empty()

    def load_build_data(self):
        self.shape_data.load_if_empty()
        self.guide_data.load_if_empty()

    def build_guides(self):

        parent = self.structure.guides

        # Build spine joints
        for i in self.get_indices():
            joint_name = naming.get_name(i, suffix=guide.SUFFIX)
            jnt_node = guide.create_guide_joint(joint_name, self.name)
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
        self.build_logic()

    def build_fk(self):
        """
        Build the FK controls for the spine and hips.
        """

        indices = self.get_indices()
        fk_builder = fk.FkControlBuilder()
        fk_builder.component_name = self.name
        fk_builder.names = [naming.get_name(i, control.SUFFIX) for i in indices]
        fk_builder.matrices = [self.guide_data.data[i] for i in indices]
        fk_builder.shape_data = [self.shape_data.data.get(i, {}) for i in indices]
        fk_builder.parent_mtx_plug = self.inputs["parent_ws"].plug
        fk_builder.build()

        cmds.parent(*fk_builder.out_controls, self.structure.controls)

        self.fk_ctrls = fk_builder.out_controls

        for i, ctrl in enumerate(self.fk_ctrls):
            self.outputs["fk_ctrls_ws"].plug[i].connect(control.get_normalized_matrix_output(ctrl))

    def build_logic(self):
        """
        Build the logic for the spine controls. The first hip control is the parent of the first spine control.
        """

        pass
