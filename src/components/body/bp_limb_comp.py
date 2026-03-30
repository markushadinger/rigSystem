from maya import cmds
from maya.api import OpenMaya

from src.components._comp_base import Component
from src.rig.data_manager import JsonDataManager
from src.rig.module.deferred_plug import TYPE_MATRIX, TYPE_MATRIX_LIST
from src.lib import guide
from src.rig.controls import control, shape
from src.lib import hierarchy
from src.lib import naming
from src.lib.nodes import Node
from src.rig.stack import Stack, ZERO
from src.rig.snippets import fk

from src.lib.math import matrix, vector


class BpLimb(Component):
    INPUTS = {
        "parent_ws": TYPE_MATRIX,
    }

    OUTPUTS = {
        "fk_ctrls_ws": TYPE_MATRIX_LIST,
        "ik_ctrl_ws": TYPE_MATRIX,
        "joints_ws": TYPE_MATRIX_LIST,
    }

    def __init__(self, name: str, side: str):
        super().__init__(name, side)

        self.aim_axis: str = "x"
        self.up_axis: str = "z"
        self.pole_vector_distance: float = 10

        self.guide_version: int = -1
        self.guide_data: JsonDataManager | None = None
        self.shape_data: JsonDataManager | None = None

        self.ik_ctrl: Node | None = None
        self.pole_ctrl: Node | None = None
        self.fk_ctrls: list[Node] = []
        self.joints: list[Node] = []

        self._indices = None

    @property
    def indices(self) -> list[naming.Name]:
        """
        Get the indices of the spine joints. The spine joints are named in the format {name}_{side}_{index}_guide.
        :return: A list of spine joint indices.
        """
        if self._indices is None:
            self._indices = [self.name.replace(index=i) for i in range(3)]
        return self._indices

    def prepare(self):
        super().prepare()

        self.outputs["fk_ctrls_ws"].length = 3
        self.outputs["joints_ws"].length = 3

        self.guide_data = JsonDataManager(
            file_path=self.context.guide_file_path(self.name.component_name),
            ver=self.guide_version,
            default=guide.DEFAULT_VALUE
        )

        self.shape_data = JsonDataManager(
            file_path=self.context.shapes_file_path(self.name.component_name),
            ver=-1,
            default=shape.DEFAULT_SHAPE_DATA
        )

    def load_guide_data(self):
        self.guide_data.load_if_empty()

    def load_build_data(self):
        self.shape_data.load_if_empty()
        self.guide_data.load_if_empty()

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
        self.build_logic()

    def build_fk(self):
        """
        Build the FK controls for the spine and hips.
        """

        guide_data = [self.guide_data.get(i) for i in self.indices]
        shape_data = [self.shape_data.get(i, {}) for i in self.indices]

        fk_builder = fk.Chain()
        fk_builder.names = [i.replace(extra="fk") for i in self.indices]
        fk_builder.matrices = guide_data
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

        start_mtx = OpenMaya.MMatrix(self.guide_data.get(self.indices[0]))
        mid_mtx = OpenMaya.MMatrix(self.guide_data.get(self.indices[1]))
        end_mtx = OpenMaya.MMatrix(self.guide_data.get(self.indices[2]))

        # ik ctrl
        ik_name = self.name.replace(extra="ik")
        ik_shape = self.shape_data.get(ik_name, default_shape)

        ik_ctrl = control.build(ik_name)
        control.add_shape_from_dict(ik_ctrl, ik_shape)

        ik_stack = Stack(ik_ctrl)
        ik_zero = ik_stack.add(ZERO)
        cmds.xform(ik_zero, worldSpace=True, matrix=end_mtx)
        cmds.parent(ik_zero, self.structure.controls)

        # pole ctrl
        pole_name = self.name.replace(extra="pole")
        pole_shape = self.shape_data.get(pole_name, default_shape)
        pole_ctrl = control.build(pole_name)
        control.add_shape_from_dict(pole_ctrl, pole_shape)

        pole_stack = Stack(pole_ctrl)
        pole_zero = pole_stack.add(ZERO)
        cmds.xform(pole_zero, worldSpace=True, matrix=mid_mtx)
        cmds.parent(pole_zero, self.structure.controls)

        a = matrix.get_point_from_matrix(start_mtx)
        b = matrix.get_point_from_matrix(mid_mtx)
        c = matrix.get_point_from_matrix(end_mtx)
        up = vector.get_normal_from_triangle(a, b, c)
        aim = (c - a).normalize()
        side = up ^ aim

        pole_mtx = matrix.get_matrix_from_axis(aim, side, up, b + side * self.pole_vector_distance)
        cmds.xform(pole_zero, worldSpace=True, matrix=pole_mtx)

    def build_logic(self):
        """
        Build the logic for the spine controls. The first hip control is the parent of the first spine control.
        """

        pass
