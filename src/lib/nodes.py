from maya import cmds
from maya.api import OpenMaya

from typing import Iterable


class Plug(str):
    def __new__(cls, node: "Node", name: str):
        obj = super().__new__(cls, f"{node}.{name}")
        obj._node = node
        obj._name = name
        return obj

    @property
    def name(self) -> str:
        return self._name

    @property
    def node(self) -> "Node":
        return self._node

    @property
    def value(self) -> any:
        return cmds.getAttr(str(self))

    @value.setter
    def value(self, v: any) -> None:
        if isinstance(v, str):
            cmds.setAttr(self, v, type="string")
            return

        if is_matrix_value(v):
            cmds.setAttr(self, *v, type="matrix")
            return

        if isinstance(v, (list, tuple)):
            if all(isinstance(i, (int, float)) for i in v):
                cmds.setAttr(self, *v)
                return

        cmds.setAttr(self, v)

    def connect(self, other: "Plug") -> None:
        """
        Connect other plug to this plug.
        :param other:
        :return:
        """
        if not isinstance(other, Plug):
            raise TypeError("Can only connect Plug to Plug")
        cmds.connectAttr(other, self, force=True)

    def __lshift__(self, other: "Plug") -> "Plug":
        self.connect(other)
        return self

    def __rshift__(self, other: "Plug") -> "Plug":
        other.connect(self)
        return self

    def __setattr__(self, key, value):
        if key.startswith("_"):
            super().__setattr__(key, value)
            return

        if hasattr(self, key):
            super().__setattr__(key, value)
            return

        cmds.setAttr(self, **{key: value})

    def __getitem__(self, key):
        return Plug(self.node, f"{self.name}[{key}]")


class Node(str):

    @classmethod
    def create(cls, node_type: str, name: str, **kwargs) -> "Node":
        """
        Create a new node of the given type and name.
        :param node_type: Type of the node to create (e.g. "transform", "multMatrix", etc.)
        :param name: Name of the node to create
        :param kwargs: Additional keyword arguments to pass to cmds.createNode (e.g. parent, etc.)
        :return: The created node as a Node instance
        """
        return cls(cmds.createNode(node_type, name=name, **kwargs))

    def __new__(cls, node: str):
        obj = super().__new__(cls, node)
        obj._node = node
        return obj

    def __getattr__(self, item: str) -> Plug:
        return Plug(self, item)


def is_matrix_value(value: any) -> bool:
    if isinstance(value, OpenMaya.MMatrix):
        return True

    if isinstance(value, Iterable) and len(value) == 16 and all(isinstance(v, (int, float)) for v in value):
        return True

    return False
