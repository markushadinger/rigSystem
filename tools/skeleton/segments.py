from src.lib.nodes import Node
from src.lib import tree
from src.lib import transform
from src.lib.naming import Name
from src.lib.math import matrix

from maya.api import OpenMaya


def split_into_segments(start: Node, end: Node, names: list[str]) -> list[Node]:
    count = len(names)
    start_point = transform.get_position(start)
    start_mtx = transform.get_matrix(start)
    start_rotation = transform.get_rotation(start)

    end_point = transform.get_position(end)
    vector = end_point - start_point
    segment_vector = vector / (count - 1)

    parent = start
    chain = list()
    for i, name in enumerate(names):
        joint = Node(name).create("joint")
        transform.set_matrix(joint, start_mtx)
        transform.set_position(joint, start_point + segment_vector * i)
        # transform.set_rotation(joint, start_rotation)
        transform.freeze(joint, apply=True)

        tree.parent(joint, parent)
        parent = joint
        chain.append(joint)

    return chain


def orient(segment: list[Node], world_up: OpenMaya.MVector, aim_axis: str, up_axis: str):
    seg_matrices = []
    for start, end in zip(segment, segment[1:]):
        start_pos = transform.get_position(start)
        end_pos = transform.get_position(end)
        aim = (end_pos - start_pos).normalize()

        mtx = matrix.get_matrix_from_aim_up_pos(
            aim, world_up, start_pos, up_axis, aim_axis
        )
        seg_matrices.append(mtx)

    end_pos = transform.get_position(segment[-1])
    end_mtx = matrix.replace_position(seg_matrices[-1], end_pos)
    seg_matrices.append(end_mtx)

    for n, mtx in zip(segment, seg_matrices):
        transform.set_matrix(n, mtx)
        transform.freeze(n, apply=True)
