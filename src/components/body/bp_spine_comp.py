from maya import cmds
from maya.api import OpenMaya

from src.components._comp_base import Component
from src.rig.data_manager import JsonDataManager
from src.rig.module.deferred_plug import MATRIX, MATRIX_LIST
from src.lib import guide
from src.rig.controls import control, shape
from src.lib import naming
from src.lib import joint
from src.lib.nodes import Node
from src.rig.snippets import fk, curve, surface, pins


class HMSpineComponent(Component):
    INPUTS = {
        "placer_ws": MATRIX,
        "parent_ws": MATRIX,
    }

    OUTPUTS = {
        "spine_ctrls_ws": MATRIX_LIST,
        "hip_ctrls_ws": MATRIX_LIST,
        "joints_ws": MATRIX_LIST,
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

        self.fk_spine_controls: list[Node] = []
        self.fk_hip_controls: list[Node] = []
        self.joints: list[Node] = []

    def get_spine_indices(self) -> list[naming.Name]:
        """
        Get the indices of the spine joints. The spine joints are named in the format {name}_{side}_{index}_guide.
        :return: A list of spine joint indices.
        """

        return [self.name.replace(index=i) for i in range(self.control_count)]

    def get_hip_indices(self) -> list[naming.Name]:
        """
        Get the indices of the hip joints. The hip joints are named in the format {name}_{side}_{index}_hip_guide.
        :return: A list of hip joint indices.
        """
        return [self.name.replace(index=i, extra="hip") for i in range(2)]

    def prepare(self):
        super().prepare()

        self.outputs["spine_ctrls_ws"].length = self.control_count
        self.outputs["hip_ctrls_ws"].length = 1
        self.outputs["joints_ws"].length = self.joint_count

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
        self.guide_data.load_if_empty()
        self.shape_data.load_if_empty()

    def build_guides(self):
        """
        Build the guide joints for the spine and hips.
        :return:
        """

        for indices in (
                self.get_spine_indices(),
                self.get_hip_indices()
        ):

            parent = self.structure.guides
            for i in indices:
                joint_node = guide.create_guide_joint(i)
                cmds.parent(joint_node, parent)

                cmds.xform(joint_node, worldSpace=True, matrix=self.guide_data.get(i))
                parent = joint_node

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
        spine_indices = self.get_spine_indices()[:-1]
        hip_indices = self.get_hip_indices()[:-1]
        out_controls = []

        for indices in (spine_indices, hip_indices):
            guide_data = [self.guide_data.get(i) for i in indices]
            shape_data = [self.shape_data.get(i) for i in indices]

            fk_builder = fk.Chain()
            fk_builder.names = indices
            fk_builder.matrices = guide_data
            fk_builder.shape_data = shape_data
            fk_builder.parent_mtx_plug = self.inputs["parent_ws"].plug
            fk_builder.parent_node = self.structure.controls
            fk_builder.build()

            out_controls.append(fk_builder.out_controls)

        self.fk_spine_controls, self.fk_hip_controls = out_controls

        for i, ctrl in enumerate(self.fk_spine_controls):
            self.outputs["spine_ctrls_ws"].plug[i].connect(control.get_normalized_matrix_output(ctrl))

        for i, ctrl in enumerate(self.fk_hip_controls):
            self.outputs["hip_ctrls_ws"].plug[i].connect(control.get_normalized_matrix_output(ctrl))

    def build_logic(self):
        """
        Build the logic for the spine controls. The first hip control is the parent of the first spine control.
        """

        end_spine_mtx = OpenMaya.MMatrix(self.guide_data.data[str(self.get_spine_indices()[-1])])
        end_spine_ctrl_mtx = OpenMaya.MMatrix(self.fk_spine_controls[-1].worldMatrix[0].value)
        end_spine_offset_mtx = end_spine_mtx * end_spine_ctrl_mtx.inverse()

        end_spine_mtx_node = Node.create("multMatrix", name=f"{self.name}_end_mtx")
        end_spine_mtx_node.matrixIn[0].value = end_spine_offset_mtx
        end_spine_mtx_node.matrixIn[1].connect(self.fk_spine_controls[-1].worldMatrix[0])

        end_hip_mtx = OpenMaya.MMatrix(self.guide_data.data[str(self.get_hip_indices()[-1])])
        end_hip_ctrl_mtx = OpenMaya.MMatrix(self.fk_hip_controls[-1].worldMatrix[0].value)
        end_hip_offset_mtx = end_hip_mtx * end_hip_ctrl_mtx.inverse()

        end_hip_mtx_node = Node.create("multMatrix", name=f"{self.name}_end_mtx")
        end_hip_mtx_node.matrixIn[0].value = end_hip_offset_mtx
        end_hip_mtx_node.matrixIn[1].connect(self.fk_hip_controls[-1].worldMatrix[0])

        fk_hip_ctrl_plugs = [ctrl.worldMatrix[0] for ctrl in reversed(self.fk_hip_controls)]
        fk_spine_ctrl_plugs = [ctrl.worldMatrix[0] for ctrl in self.fk_spine_controls]

        # build matrix plug list and drive surface with it
        mtx_plugs = [end_hip_mtx_node.matrixSum]
        mtx_plugs.extend(fk_hip_ctrl_plugs[:-1])
        mtx_plugs.extend(fk_spine_ctrl_plugs)
        mtx_plugs.extend([end_spine_mtx_node.matrixSum])

        surface_builder = surface.MatrixRibbonBuilder()
        surface_builder.surface_name = f"{self.name}_surf"
        surface_builder.in_matrix_plugs = mtx_plugs
        surface_builder.degree = 4
        surface_builder.build()

        cmds.parent(surface_builder.out_surface_transform, self.structure.logic)

        # create joints and connect them to the surface with uv pins
        u_mapping = [i / (self.joint_count - 1) for i in range(self.joint_count)]
        for i in range(self.joint_count):
            joint_name = self.name.replace(index=i, suffix=joint.SKIN_SUFFIX)
            jnt = joint.create(joint_name)
            cmds.parent(jnt, self.structure.deform)
            self.joints.append(jnt)

        uv_pin_builder = pins.UvPinBuilder()
        uv_pin_builder.pin_name = f"{self.name}_uv_pin"
        uv_pin_builder.surface_shape = surface_builder.out_surface_shape
        uv_pin_builder.build()

        uv_pin_builder.out_pin.normalAxis.value = "xzy".index(self.aim_axis)
        uv_pin_builder.out_pin.tangentAxis.value = "xzy".index(self.up_axis)

        uv_driver = pins.UvPinTransformDriver()
        uv_driver.pin = uv_pin_builder.out_pin
        uv_driver.transforms = self.joints
        uv_driver.uv_values = [(u, 0.5) for u in u_mapping]
        uv_driver.connection_type = pins.ConnectionType.OFFSET_PARENT_MATRIX
        uv_driver.build()

        self.joints[-1].offsetParentMatrix.connect(end_spine_mtx_node.matrixSum)
        self.joints[0].offsetParentMatrix.connect(end_hip_mtx_node.matrixSum)

        curve_builder = curve.MatrixDrivenCurveBuilder()
        curve_builder.name = f"{self.name}_curve"
        curve_builder.in_matrix_plugs = [jnt.worldMatrix[0] for jnt in self.joints]
        curve_builder.degree = 3
        curve_builder.build()

        cmds.parent(curve_builder.our_transform_node, self.structure.logic)

        for i, jnt in enumerate(self.joints):
            self.outputs["joints_ws"].plug[i].connect(control.get_normalized_matrix_output(jnt))
