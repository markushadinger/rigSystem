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

        self.match_start_axis: str | None = None

    def build(self, node: Node):
        guide_matrices = [
            guide.get_world_matrix(self.name.replace(index=self.start_index)),
            guide.get_world_matrix(self.name.replace(index=self.pole_index)),
            guide.get_world_matrix(self.name.replace(index=self.end_index))]
        mtx = ik.get_pole_vector_matrix(*guide_matrices, self.distance)

        stack = Stack(node)
        zero = stack.get_by_suffix(ZERO)

        if not zero:
            zero = stack.insert(0, ZERO)

        cmds.xform(zero, worldSpace=True, matrix=mtx)

        if self.orient_to_world_space:
            cmds.xform(zero, worldSpace=True, rotation=(0, 0, 0))
            cmds.xform(zero, worldSpace=True, scale=(1, 1, 1))

        if self.match_start_axis:
            match_index = "xyz".index(self.match_start_axis)
            world_pos = [mtx[12], mtx[13], mtx[14]]
            world_pos[match_index] = guide_matrices[0][12 + match_index]
            cmds.xform(zero, worldSpace=True, translation=world_pos)
            cmds.xform(node, worldSpace=True, translation=(mtx[12], mtx[13], mtx[14]))
