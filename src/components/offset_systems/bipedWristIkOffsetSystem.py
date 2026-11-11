from maya import cmds
from maya.api import OpenMaya

from src.lib.math import matrix
from src.lib.nodes import Node
from src.lib import guide
from src.lib.naming import Name
from src.rig.stack import Stack, ZERO


class BipedWristIkOffsetSystem:

    def __init__(self, name: Name):
        self.name = name
        self.axis_flip_mapping: list = []

        self.indices = []

    def build(self, node: Node):
        stack = Stack(node)
        zero = stack.get_by_suffix(ZERO)

        current_mtx = zero.worldMatrix[0].value
        dst_mtx = [None] * 4
        dst_mtx[3] = current_mtx[12:]

        guide_matrices = [guide.get_world_matrix(self.name.replace(index=i)) for i in self.indices]
        end_point = self.get_end_point(guide_matrices)

        for src_axis, dst_axis, invert in self.axis_flip_mapping:
            src_row = "xyz".index(src_axis)
            dst_row = "xyz".index(dst_axis)

            src_row_data = current_mtx[4 * src_row: 4 * src_row + 4]
            dst_mtx[dst_row] = [v * (-1 if invert else 1) for v in src_row_data]

        control_matrix = [j for sub in dst_mtx for j in sub]
        cmds.xform(zero, worldSpace=True, rotation=(0, 0, 0), translation=list(end_point)[:-1], scale=(1, 1, 1))
        cmds.xform(node, worldSpace=True, matrix=control_matrix)
        cmds.xform(node, worldSpace=True, scale=(1, 1, 1))

    def get_end_point(self, matrices: list[OpenMaya.MMatrix]) -> OpenMaya.MMatrix:
        points = [OpenMaya.MPoint(*list(m)[12:-1]) for m in matrices]
        direction = OpenMaya.MVector.kXaxisVector * (1 if (points[-1] - points[0]).x > 0 else -1)
        distances = [p0.distanceTo(p1) for p0, p1 in zip(points, points[1:])]
        distance = sum(distances)

        return points[0] + direction * distance
