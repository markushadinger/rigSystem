from maya import cmds

from src.lib import guide
from src.rig.module.deferred_plug import TYPE_MATRIX, TYPE_FLOAT
from src.rig.controls import control, shape
from src.lib import attributes
from src.lib import hierarchy
from src.lib import naming
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

    def __init__(self, name):
        super().__init__(name)

        self.guide_version = -1
        self.guide_data: JsonDataManager | None = None
        self.shape_data: JsonDataManager | None = None

        self.control: Node | None = None
        self.joint: Node | None = None

    def prepare(self):
        super().prepare()
        self.guide_data = JsonDataManager(self.context.guide_file_path(self.name), self.guide_version)
        self.shape_data = JsonDataManager(self.context.shapes_file_path(self.name), self.guide_version)

    def load_guide_data(self):
        self.guide_data.load_if_empty()

    def load_build_data(self):
        self.guide_data.load_if_empty()
        self.shape_data.load_if_empty()

    def build_guides(self):
        joint_node = guide.create_guide_joint(naming.get_name(self.name, suffix=guide.SUFFIX), self.name)
        cmds.parent(joint_node, str(self.structure.guides))

        # import guide data
        hierarchy.match_nodes_to_matrices({guide.get_name(self.name): m for n, m in self.guide_data.data.items()})

    def build(self):
        self.build_controls()
        self.build_joints()

    def build_controls(self):
        shape_node = shape.create(**self.shape_data.data.get(self.name, shape.DEFAULT_SHAPE_DATA))

        self.control = control.build(control.get_name(self.name), self.name)
        shape.assign_shape_to_transform(shape_node, self.control)
        cmds.parent(self.control, str(self.structure.controls))

        self.control.inParentMatrix.connect(self.inputs["parent_ws"].plug)
        self.control.inOffsetMatrix.value = self.guide_data.data[self.name]

        attributes.lock_and_hide_attr(self.control, attributes.VISIBILITY_ATTR)
        attributes.lock_and_hide_attr(self.control, attributes.SCALE_ATTRS)

        self.outputs["control_ws"].plug.connect(control.get_normalized_matrix_output(self.control))

    def build_joints(self):
        joint_name = naming.get_name(self.name, suffix=joint.SKIN_SUFFIX)
        jnt = joint.create(joint_name, self.name)
        cmds.parent(jnt, str(self.structure.deform))

        jnt.offsetParentMatrix.connect(self.control.worldMatrix[0])
        jnt.inheritsTransform.value = False
        self.outputs["joint_ws"].plug.connect(jnt.worldMatrix[0])
