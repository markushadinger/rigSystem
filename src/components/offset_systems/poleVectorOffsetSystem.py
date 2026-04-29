from maya.api import OpenMaya
from maya import cmds

from src.lib.nodes import Node
from src.rig.data_manager import GuideDataManager
from src.rig.snippets import ik
from src.rig.stack import Stack, ZERO
from src.lib import guide


class PoleVectorOffsetSystem:

    def __init__(self, name):
        self.name = name
        self.distance: float = 10
        self.guide_data: GuideDataManager | None = None
        self.start_index: str | None = None
        self.end_index: str | None = None
        self.pole_index: str | None = None

    def build(self, node: Node):
        mtx = ik.get_pole_vector_matrix(
            OpenMaya.MMatrix(guide.get_world_matrix(self.name.replace(index=self.start_index))),
            OpenMaya.MMatrix(guide.get_world_matrix(self.name.replace(index=self.pole_index))),
            OpenMaya.MMatrix(guide.get_world_matrix(self.name.replace(index=self.end_index))),
            self.distance
        )

        stack = Stack(node)
        zero = stack.get_by_suffix(ZERO)

        if not zero:
            zero = stack.insert(0, ZERO)

        cmds.xform(zero, worldSpace=True, matrix=mtx)
