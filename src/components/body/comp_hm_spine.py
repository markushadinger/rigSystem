from src.components._comp_base import Component
from src.rig.data_manager import JsonDataManager
from src.rig.module.deferred_plug import TYPE_MATRIX
from src.lib import guide
from src.rig.controls import color, control, shape
from src.lib import hierarchy
from src.lib import naming
from src.lib.nodes import Node

from src.rig.snippets import fk, curve, surface

from maya import cmds
from maya.api import OpenMaya


class HMSpineComponent(Component):
    INPUTS = {
        "placer_ws": TYPE_MATRIX,
        "parent_ws": TYPE_MATRIX,
    }

    OUTPUTS = {
        "control_ws": TYPE_MATRIX,
        "control_ls": TYPE_MATRIX,
        "control_rs": TYPE_MATRIX,
    }

    def __init__(self, name):
        super().__init__(name)

        self.side = "m"
        self.control_count: int = 5
        self.joint_count: int = 10

        self.guide_version: int = -1
        self.guide_data: JsonDataManager | None = None

        self.fk_spine_controls: list[Node] = []
        self.fk_hip_controls: list[Node] = []

    def get_spine_indices(self) -> list[str]:
        """
        Get the indices of the spine joints. The spine joints are named in the format {name}_{side}_{index}_guide.
        :return: A list of spine joint indices.
        """
        return [naming.get_name(self.name, self.side, i) for i in range(self.control_count)]

    def get_hip_indices(self) -> list[str]:
        """
        Get the indices of the hip joints. The hip joints are named in the format {name}_{side}_{index}_hip_guide.
        :return: A list of hip joint indices.
        """
        return [naming.get_name(self.name, self.side, i, "hip") for i in range(2)]

    def prepare(self):
        super().prepare()
        self.guide_data = JsonDataManager(self.context.guide_file_path(self.name), self.guide_version)

    def load_guide_data(self):
        self.guide_data.load()

    def build_guides(self):

        # Build spine joints
        parent = self.structure.guides
        for i in self.get_spine_indices():
            joint_name = naming.get_name(i, suffix=guide.GUIDE_SUFFIX)
            joint = guide.create_guide_joint(joint_name, self.name)
            cmds.parent(joint, parent)
            parent = joint

        # Build hip joints
        parent = self.structure.guides
        for i in self.get_hip_indices():
            joint_name = naming.get_name(i, suffix=guide.GUIDE_SUFFIX)
            joint = guide.create_guide_joint(joint_name, self.name)
            cmds.parent(joint, parent)
            parent = joint

        # assign guide data to joints
        guide_data_dict = {guide.get_name(n): m for n, m in self.guide_data.data.items()}
        hierarchy.match_nodes_to_matrices(guide_data_dict)

    def build(self):
        """
        Build the spine controls.
        :return:
        """

        self.build_fk()
        self.build_hip()
        self.build_logic()

    def build_fk(self):
        """
        Build FK controls for the spine. The number of controls is determined by self.control_count.
        The controls are evenly distributed along the spine joints.
        """

        spine_indices = self.get_spine_indices()
        fk_spine_ctrl_names = [naming.get_name(i, control.SUFFIX) for i in spine_indices[:-1]]
        fk_spine_ctrl_mtxs = [self.guide_data.data[i] for i in spine_indices[:-1]]
        self.fk_spine_controls = fk.build_fk_controls(
            fk_spine_ctrl_names,
            fk_spine_ctrl_mtxs,
            self.inputs["parent_ws"].plug,
            self.structure.controls
        )

    def build_hip(self):
        """
        Build hip control. The hip control is the parent of the first spine control and is used to drive the entire spine.
        """

        hip_indices = self.get_hip_indices()
        fk_hip_ctrl_names = [naming.get_name(i, control.SUFFIX) for i in hip_indices[:-1]]
        fk_hip_ctrl_mtxs = [self.guide_data.data[i] for i in hip_indices[:-1]]
        self.fk_hip_controls = fk.build_fk_controls(
            fk_hip_ctrl_names,
            fk_hip_ctrl_mtxs,
            self.inputs["parent_ws"].plug,
            self.structure.controls
        )

    def build_logic(self):
        """
        Build the logic for the spine controls. The first hip control is the parent of the first spine control.
        """

        # # create point for the end of the hip to drive the curve.
        # hip_end_mtx = OpenMaya.MMatrix(self.guide_data.data[self.get_hip_indices()[-1]])
        # hip_last_ctrl_mtx = OpenMaya.MMatrix(self.fk_hip_controls[-1].worldMatrix[0].value)
        # hip_end_pnt = list(hip_end_mtx * hip_last_ctrl_mtx.inverse())[12:15]

        # hip_end_pnt_node = Node.create("multiplyPointByMatrix", name=f"{self.name}_hip_end_mlt")
        # hip_end_pnt_node.input.value = hip_end_pnt
        # hip_end_pnt_node.matrix.connect(self.fk_hip_controls[-1].worldMatrix[0])

        # # create point for the end of the spine to drive the curve.
        # spine_end_mtx = OpenMaya.MMatrix(self.guide_data.data[self.get_spine_indices()[-1]])
        # spine_last_ctrl_mtx = OpenMaya.MMatrix(self.fk_spine_controls[-1].worldMatrix[0].value)
        # spine_end_pnt = list(spine_end_mtx * spine_last_ctrl_mtx.inverse())[12:15]

        # spine_end_pnt_node = Node.create("multiplyPointByMatrix", name=f"{self.name}_hip_end_mlt")
        # spine_end_pnt_node.input.value = spine_end_pnt
        # spine_end_pnt_node.matrix.connect(self.fk_spine_controls[-1].worldMatrix[0])

        # transform_plugs = [hip_end_pnt_node.output]

        # spine_plugs = [ctrl.worldMatrix[0] for ctrl in self.fk_spine_controls]
        # hip_plugs = [ctrl.worldMatrix[0] for ctrl in reversed(self.fk_hip_controls[1:])]

        # for plug in hip_plugs + spine_plugs:
        #     trf_node = Node.create("translationFromMatrix", name=f"{self.name}_{plug.node}_tf")
        #     trf_node.input.connect(plug)
        #     transform_plugs.append(trf_node.output)

        # transform_plugs.append(spine_end_pnt_node.output)
        # curve.build_matrix_driven_curve(f"{self.name}_spine_crv", transform_plugs)

        end_spine_mtx = OpenMaya.MMatrix(self.guide_data.data[self.get_spine_indices()[-1]])
        end_spine_ctrl_mtx = OpenMaya.MMatrix(self.fk_spine_controls[-1].worldMatrix[0].value)
        end_spine_offset_mtx = end_spine_mtx * end_spine_ctrl_mtx.inverse()

        end_spine_mtx_node = Node.create("multMatrix", name=f"{self.name}_end_mtx")
        end_spine_mtx_node.matrixIn[0].value = end_spine_offset_mtx
        end_spine_mtx_node.matrixIn[1].connect(self.fk_spine_controls[-1].worldMatrix[0])

        end_hip_mtx = OpenMaya.MMatrix(self.guide_data.data[self.get_hip_indices()[-1]])
        end_hip_ctrl_mtx = OpenMaya.MMatrix(self.fk_hip_controls[-1].worldMatrix[0].value)
        end_hip_offset_mtx = end_hip_mtx * end_hip_ctrl_mtx.inverse()

        end_hip_mtx_node = Node.create("multMatrix", name=f"{self.name}_end_mtx")
        end_hip_mtx_node.matrixIn[0].value = end_hip_offset_mtx
        end_hip_mtx_node.matrixIn[1].connect(self.fk_hip_controls[-1].worldMatrix[0])

        fk_hip_ctrl_plugs = [ctrl.worldMatrix[0] for ctrl in reversed(self.fk_hip_controls)]
        fk_spine_ctrl_plugs = [ctrl.worldMatrix[0] for ctrl in self.fk_spine_controls]

        mtx_plugs = [end_hip_mtx_node.matrixSum] + fk_hip_ctrl_plugs[:-1] + fk_spine_ctrl_plugs + [end_spine_mtx_node.matrixSum]
        surface.create_matrix_driven_surface(f"{self.name}_spine_surf", mtx_plugs)
