from src.lib.nodes import Node
from maya import cmds

from typing import Iterable


def is_dag_node(node: Node) -> bool:
    return cmds.objectType(node, isType="transform")


def parent(child: Node | Iterable[Node], parent: Node):
    cmds.parent(child, parent)


def unparent(child: Node | Iterable[Node]):
    cmds.parent(child, world=True)


def get_parent(node: Node) -> Node | None:
    parent: str = (cmds.listRelatives(node, parent=True) or [None])[0]

    if not parent:
        return

    return Node(parent)


def is_root_node(node: Node) -> bool:
    return get_parent(node) is None


def get_children(node: Node) -> list[Node]:
    return [Node(s) for s in cmds.listRelatives(node, children=True, shapes=False) or []]


def is_child_of(child: Node, parent: Node) -> bool:
    while child := get_parent(child):
        if child == parent:
            return True

    return False


def get_chain_between(start: Node, end: Node) -> list[Node] | None:
    chain = []
    current = end

    while current:
        chain.append(current)
        if current == start:
            return chain[::-1]
        current = get_parent(current)

    return None


def get_node_depth(node: Node) -> int:
    depth = 0
    while node := get_parent(node):
        depth += 1
    return depth


def get_shape(node: Node) -> Node | None:
    shape = (cmds.listRelatives(node, children=True, shapes=True) or [None])[0]

    if not shape:
        return None

    return Node(shape)


def parent_shape(shape: Node, parent: Node):
    cmds.parent(shape, parent, relative=True, shape=True)


def get_siblings(node: Node) -> list[Node]:
    parent = get_parent(node)

    if not parent:
        return list()

    return [c for c in get_children(parent) if c != node]
