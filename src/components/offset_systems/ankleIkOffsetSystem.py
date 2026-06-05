
from maya import cmds
from maya.api import OpenMaya

from src.lib.math import matrix
from src.lib.nodes import Node
from src.lib import guide
from src.lib.naming import Name
from src.rig.stack import Stack, ZERO


class AnkleIkOffsetSystem:

    def __init__(self, name: Name):
        self.name = name
        self.aim_vector: OpenMaya.MVector = OpenMaya.MVector.kXaxisVector
        self.up_vector: OpenMaya.MVector = OpenMaya.MVector.kZaxisVector
        self.aim_axis: str = "x"
        self.up_axis: str = "z"
        self.control_up_axis: str = "x"

        self.hip_index: str = "hip"

    def build(self, node: Node):
        stack = Stack(node)
        zero = stack.get_by_suffix(ZERO)

        hip_matrix = list(guide.get_world_matrix(self.name.replace(index=self.hip_index)))
        current_mtx = zero.worldMatrix[0].value
        control_up_row = "xyz".index(self.control_up_axis)

        up_vector = OpenMaya.MVector(current_mtx[control_up_row * 4: control_up_row * 4 + 3])
        zero_pnt = OpenMaya.MPoint(hip_matrix[12], current_mtx[13], hip_matrix[14])

        zero_mtx = matrix.get_matrix_from_aim_up_pos(
            aim_vector=self.aim_vector,
            up_vector=self.up_vector,
            up_axis=self.up_axis,
            aim_axis=self.aim_axis,
            pos=zero_pnt
        )

        control_mtx = matrix.get_matrix_from_aim_up_pos(
            aim_vector=self.aim_vector,
            up_vector=up_vector,
            up_axis=self.up_axis,
            aim_axis=self.aim_axis,
            pos=OpenMaya.MPoint(current_mtx[12:-1])
        )

        cmds.xform(zero, worldSpace=True, matrix=zero_mtx)
        cmds.xform(node, worldSpace=True, matrix=control_mtx)