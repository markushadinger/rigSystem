from maya import cmds

from src.rig.controls import control, shape
from src.rig.stack import Stack
from src.lib.nodes import Plug, Node
from src.lib.naming import Name


class Chain:
    def __init__(self):
        self.names: list[Name] = []
        self.matrices: list = []
        self.shape_data: list[dict] | None = None
        self.parent_mtx_plug: Plug | None = None
        self.parent_node: Node | None = None

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
        parent_plug = self.parent_mtx_plug

        for name, matrix, shp in zip(self.names, self.matrices, shape_data):
            # create control and shape
            ctrl_node = control.build(name)
            shape_node = shape.create(**shp)
            shape.assign_shape_to_transform(shape_node, ctrl_node)

            stack = Stack(ctrl_node)
            zero = stack.insert(0, "zero")

            zero.offsetParentMatrix.connect(parent_plug)
            cmds.xform(zero, worldSpace=True, matrix=matrix)
            cmds.parent(zero, self.parent_node)

            parent_plug = ctrl_node.worldMatrix[0]
            self.out_controls.append(ctrl_node)
