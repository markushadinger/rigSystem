from maya import cmds

from src.lib.nodes import Node
from src.lib import naming

ZERO = "zero"
AUTOMATION = "auto"
SPACESWITCH = "spsw"


class Stack:

    def __init__(self, target: Node):
        self._target = target
        self._stack: list[Node] = []

    def add(self, suffix) -> Node:
        return self.insert(-1, suffix)

    def insert(self, index: int, suffix: str) -> Node:
        index = index if index >= 0 else len(self._stack) + index + 1

        if index < 0:
            raise IndexError(f"Invalid Index {index}")

        element = _build_element(self._target, suffix)

        self._stack.insert(index, element)

        if index > 0:
            parent = self._stack[index - 1]
            cmds.parent(element, parent)

        if index < len(self._stack) - 1:
            child = self._stack[index + 1]
            cmds.parent(child, element)

        if index == len(self._stack) - 1:
            cmds.parent(self._target, element)

        return element


def _build_element(target: Node, suffix: str):
    root_name = naming.strip_suffix(target)
    element_name = naming.get_name(root_name, suffix)
    return Node.create("transform", name=element_name)
