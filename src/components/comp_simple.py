from maya import cmds

from src.lib import guide
from src.rig.module.deferred_plug import TYPE_MATRIX, TYPE_FLOAT
from src.rig.controls import color, control, shape
from src.lib.nodes import Plug, Node
from src.lib import attributes
from src.lib import hierarchy
from src.rig.data_manager import JsonDataManager
from src.components._comp_base import Component


class SimpleComponent(Component):
    INPUTS = {
        "parent_ws": TYPE_MATRIX,
    }

    OUTPUTS = {
        "control_ws": TYPE_MATRIX,
        "control_ls": TYPE_MATRIX,
        "control_rs": TYPE_MATRIX,
        "scale_factor": TYPE_FLOAT,
    }

    def __init__(self, name):
        super().__init__(name)

        self.guide_version = -1
        self.guide_data: JsonDataManager | None = None

    def prepare(self):
        super().prepare()
        self.guide_data = JsonDataManager(self.context.guide_file_path(self.name), self.guide_version)

    def load_guide_data(self):
        self.guide_data.load()

    def build_guides(self):
        joint = guide.create_guide_joint(guide.get_name(self.name), self.name)
        cmds.parent(joint, str(self.structure.guides))

        # import guide data
        hierarchy.match_nodes_to_matrices({guide.get_name(self.name): m for n, m in self.guide_data.data.items()})

    def build(self):
        ctrl = control.build(control.get_name(self.name), self.name)
        cmds.parent(ctrl, str(self.structure.controls))

        ctrl.inParentMatrix.connect(self.inputs["parent_ws"].plug)
        ctrl.inOffsetMatrix.value = self.guide_data.data[self.name]

        attributes.lock_and_hide_attr(ctrl, attributes.VISIBILITY_ATTR)
        attributes.lock_and_hide_attr(ctrl, attributes.SCALE_ATTRS)

        shape.set_shape(ctrl, shape.scale_shape(shape.CIRCLE, 30))
        shape.set_color(ctrl, shape.COLOR_YELLOW)

        self.outputs["control_ws"].plug.connect(control.get_normalized_matrix_output(ctrl))
        self.outputs["control_ls"].plug.connect(ctrl.matrix)
        self.outputs["scale_factor"].plug.connect(ctrl.sy)
