from maya import cmds
from maya.api import OpenMaya
from maya.api.OpenMaya import MMatrix

from src.lib.math import matrix
from src.lib.nodes import Node
from src.lib import guide
from src.lib.naming import Name
from src.rig.stack import Stack, ZERO


class FkStraightOffsetSystem:

    def __init__(self, name: Name):
        self.name = name
        self.default_matrix: MMatrix = MMatrix.kIdentity
        self.prev_index: str | None = None

    def build(self, node: Node):
        stack = Stack(node)
        zero = stack.get_by_suffix(ZERO)

        control_mtx = MMatrix(node.worldMatrix[0].value)

        if not self.prev_index:
            zero_mtx = MMatrix(self.default_matrix)
        else:
            zero_mtx = guide.get_world_matrix(self.name.replace(index=self.prev_index))

        zero_mtx[12] = control_mtx[12]
        zero_mtx[13] = control_mtx[13]
        zero_mtx[14] = control_mtx[14]

        cmds.xform(zero, worldSpace=True, matrix=zero_mtx)
        cmds.xform(node, worldSpace=True, matrix=control_mtx)
        return
