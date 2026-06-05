from maya import cmds

from src.lib.nodes import Node
from src.rig.snippets import ik
from src.rig.stack import Stack, ZERO
from src.lib import guide


class PoleVectorOffsetSystem:

    def __init__(self, name):
        self.name = name
        self.distance: float = 10
        self.start_index: str | None = None
        self.end_index: str | None = None
        self.pole_index: str | None = None
        self.orient_to_world_space: bool = True

    def build(self, node: Node):
        mtx = ik.get_pole_vector_matrix(
            guide.get_world_matrix(self.name.replace(index=self.start_index)),
            guide.get_world_matrix(self.name.replace(index=self.pole_index)),
            guide.get_world_matrix(self.name.replace(index=self.end_index)),
            self.distance
        )

        stack = Stack(node)
        zero = stack.get_by_suffix(ZERO)

        if not zero:
            zero = stack.insert(0, ZERO)

        cmds.xform(zero, worldSpace=True, matrix=mtx)

        if self.orient_to_world_space:
            cmds.xform(zero, worldSpace=True, rotation=(0, 0, 0))
