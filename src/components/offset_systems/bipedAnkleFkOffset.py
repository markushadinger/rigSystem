from maya import cmds
from maya.api import OpenMaya
from maya.api.OpenMaya import MVector

from src.lib.math import matrix
from src.lib.nodes import Node
from src.lib import guide
from src.lib.naming import Name
from src.rig.stack import Stack, ZERO


class BipedAnkleFkOffsetSystem:

    def __init__(self, name: Name):
        self.name = name
        self.knee_index: str | None = None
        self.ankle_index: str | None = None
        self.aim_axis: str = "x"
        self.aim_vector: MVector = MVector.kYnegAxisVector
        self.up_axis: str = "y"
        self.flip_x: bool = False
        self.flip_y: bool = False
        self.flip_z: bool = False

    def build(self, node: Node):
        stack = Stack(node)
        zero = stack.get_by_suffix(ZERO)

        knee_mtx = list(guide.get_world_matrix(self.name.replace(index=self.knee_index)))
        ankle_mtx = list(guide.get_world_matrix(self.name.replace(index=self.ankle_index)))

        zero_mtx = list(knee_mtx)
        zero_mtx[12] = ankle_mtx[12]
        zero_mtx[13] = ankle_mtx[13]
        zero_mtx[14] = ankle_mtx[14]

        ankle_pos = OpenMaya.MPoint(ankle_mtx[12:-1])
        up_vector = MVector(ankle_mtx[0:3])

        ctrl_mtx = matrix.get_matrix_from_aim_up_pos(
            aim_vector=self.aim_vector,
            up_vector=up_vector,
            up_axis=self.up_axis,
            aim_axis=self.aim_axis,
            pos=ankle_pos
        )

        ctrl_mtx = list(ctrl_mtx)
        for i in range(3):
            ctrl_mtx[0 + i] = -ctrl_mtx[0 + i] if self.flip_x else ctrl_mtx[0 + i]
            ctrl_mtx[4 + i] = -ctrl_mtx[4 + i] if self.flip_y else ctrl_mtx[4 + i]
            ctrl_mtx[8 + i] = -ctrl_mtx[8 + i] if self.flip_z else ctrl_mtx[8 + i]

        cmds.xform(zero, worldSpace=True, matrix=zero_mtx)
        cmds.xform(node, worldSpace=True, matrix=ctrl_mtx)
