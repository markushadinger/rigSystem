from maya import cmds

from src.lib import guide
from src.rig.module.deferred_plug import TYPE_MATRIX
from src.rig.controls import control, shape
from src.rig.stack import Stack
from src.lib import attributes
from src.lib import joint
from src.lib.nodes import Node
from src.rig.data_manager import JsonDataManager
from src.components._comp_base import Component


class SimpleComponent(Component):
    INPUTS = {
        "parent_ws": TYPE_MATRIX,
    }

    OUTPUTS = {
        "control_ws": TYPE_MATRIX,
        "joint_ws": TYPE_MATRIX,
    }

    def __init__(self, name: str, side: str | None):
        super().__init__(name, side)

        self.guide_version = -1
        self.guide_data: JsonDataManager | None = None
        self.shape_data: JsonDataManager | None = None

        self.control: Node | None = None
        self.joint: Node | None = None

    def prepare(self):
        super().prepare()
        self.guide_data = JsonDataManager(
            file_path=self.context.guide_file_path(self.name),
            ver=self.guide_version,
            default=guide.DEFAULT_VALUE
        )

        self.shape_data = JsonDataManager(
            file_path=self.context.shapes_file_path(self.name),
            ver=-1,
            default=shape.DEFAULT_SHAPE_DATA
        )

    def load_guide_data(self):
        self.guide_data.load_if_empty()

    def load_build_data(self):
        self.guide_data.load_if_empty()
        self.shape_data.load_if_empty()

    def build_guides(self):
        joint_node = guide.create_guide_joint(self.name)
        cmds.parent(joint_node, str(self.structure.guides))

        guide_data = self.guide_data.get(self.name, guide.DEFAULT_VALUE)
        cmds.xform(joint_node, worldSpace=True, matrix=guide_data)

    def build(self):
        self.build_controls()
        self.build_joints()

    def build_controls(self):
        shape_data = self.shape_data.get(self.name)

        shape_node = shape.create(**shape_data)
        self.control = control.build(self.name)
        shape.assign_shape_to_transform(shape_node, self.control)

        stack = Stack(self.control)
        zero = stack.insert(0, "zero")

        cmds.parent(zero, self.structure.controls)
        cmds.xform(zero, worldSpace=True, matrix=self.guide_data.get(self.name, guide.DEFAULT_VALUE))
        zero.offsetParentMatrix.connect(self.inputs["parent_ws"].plug)

        attributes.lock_and_hide_attr(self.control, attributes.VISIBILITY_ATTR)
        attributes.lock_and_hide_attr(self.control, attributes.SCALE_ATTRS)

        self.outputs["control_ws"].plug.connect(control.get_normalized_matrix_output(self.control))

    def build_joints(self):
        jnt = joint.create(self.name.replace(suffix=joint.SKIN_SUFFIX))
        cmds.parent(jnt, self.structure.deform)

        jnt.offsetParentMatrix.connect(self.control.worldMatrix[0])
        jnt.inheritsTransform.value = False
        self.outputs["joint_ws"].plug.connect(jnt.worldMatrix[0])
