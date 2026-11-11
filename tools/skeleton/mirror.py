from src.lib.nodes import Node
from src.lib import tree
from src.lib import transform
from src.lib.naming import Name

from maya.api import OpenMaya

MIRROR_MATRIX = OpenMaya.MMatrix([
    -1, 0, 0, 0,
    0, 1, 0, 0,
    0, 0, 1, 0,
    0, 0, 0, 1
])


def flip(nodes: list[Node]):
    nodes.sort(key=tree.get_node_depth)
    flip_matrices = [transform.get_matrix(n) * MIRROR_MATRIX for n in nodes]

    for n, mtx in zip(nodes, flip_matrices):
        transform.set_matrix(n, mtx)


def mirror(nodes: list[Node]):
    nodes.sort(key=tree.get_node_depth, reverse=False)
    other_nodes = [str(n.replace("_r_", "_l_")) for n in nodes]
    mirror_matrices = [transform.get_matrix(n) * MIRROR_MATRIX for n in other_nodes]

    for n, mtx in zip(nodes, mirror_matrices):
        n.jointOrient.value = [0, 0, 0]
        transform.set_matrix(n, mtx)
        transform.freeze(n, apply=True)
