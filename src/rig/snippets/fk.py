from maya import cmds

from src.rig.controls import control, shape
from src.lib.nodes import Plug, Node


class FkControlBuilder:
    def __init__(self):
        self.component_name = ""
        self.names: list[str] = []
        self.matrices: list = []
        self.shape_data: list[dict] | None = None
        self.parent_mtx_plug: Plug | None = None

        self.out_controls: list[Node] = []

    def get_normalized_shape_data(self) -> list[dict]:
        """
        Get normalized shape data. This is to ensure that the shape data is in the correct format for the shape creation.
        :param data: The shape data to normalize.
        """
        shape_data = [shape.DEFAULT_SHAPE_DATA] * len(self.names)
        if self.shape_data:
            for i, d in enumerate(self.shape_data):
                if d:
                    shape_data[i].update(d)

        return shape_data

    def build(self):
        # prep data
        shape_data = self.get_normalized_shape_data()
        parent_ctrl: None | Node = None

        for name, matrix, shp in zip(self.names, self.matrices, shape_data):

            # create control and shape
            ctrl_node = control.build(name, self.component_name)
            shape_node = shape.create(**shp)
            shape.assign_shape_to_transform(shape_node, ctrl_node)

            ctrl_node.inOffsetMatrix.value = matrix

            # connect to parent
            if parent_ctrl:
                control.set_parent_control(ctrl_node, parent_ctrl)
            elif self.parent_mtx_plug:
                ctrl_node.inParentMatrix.connect(self.parent_mtx_plug)

            parent_ctrl = ctrl_node
            self.out_controls.append(ctrl_node)
