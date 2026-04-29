from typing import Iterable, Callable

from maya import cmds
from maya.api import OpenMaya

from src.lib.naming import Name


class Plug(str):
    def __new__(cls, node: "Node", name: str):
        obj = super().__new__(cls, f"{node}.{name}")
        obj._node = node
        obj._name = name
        return obj

    @classmethod
    def from_string(cls, plug: str) -> "Plug":
        node, attr = plug.split(".", 1)
        return Plug(node, attr)

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

    def get_in_connection(self) -> "Plug":
        """
        returns the src plug connected to this Plug
        :return:
        """

        plug: str | None = (cmds.listConnections(self, source=False, destination=True, plugs=True) or [None])[0]

        if plug is None:
            return

        return self.from_string(plug)

    def get_out_connections(self) -> list["Plug"]:
        """
        returns the dst plugs connected to this Plug
        :return:
        """

        plugs: list[str] = cmds.listConnections(self, source=True, destination=False, plugs=True) or []
        return [self.from_string(p) for p in plugs]

    def connect(self, other: "Plug") -> None:
        """
        Connect other plug to this plug.
        :param other:
        :return:
        """
        if not isinstance(other, Plug):
            raise TypeError("Can only connect Plug to Plug")
        cmds.connectAttr(other, self, force=True)

    def exists(self) -> bool:
        return cmds.objExists(self)

    def __setattr__(self, key, value):
        if key.startswith("_"):
            super().__setattr__(key, value)
            return

        if hasattr(self, key):
            super().__setattr__(key, value)
            return

        cmds.setAttr(self, **{key: value})

    def __getitem__(self, key: int) -> "Plug":
        return Plug(self.node, f"{self.name}[{key}]")

    def __getattr__(self, item: str) -> "Plug":
        return Plug(self.node, f"{self.name}.{item}")


class Node(str):

    @classmethod
    def create(cls, node_type: str, name: str | Name, **kwargs) -> "Node":
        """
        Create a new node of the given type and name.
        :param node_type: Type of the node to create (e.g. "transform", "multMatrix", etc.)
        :param name: Name of the node to create
        :param kwargs: Additional keyword arguments to pass to cmds.createNode (e.g. parent, etc.)
        :return: The created node as a Node instance
        """
        return cls(cmds.createNode(node_type, name=str(name), **kwargs))

    @classmethod
    def generate(cls, generator: Callable, name: str | Name, **kwargs) -> "Node":
        """
        Generate a node using the given generator function and name.
        The generator function should take a name and return the name of the created node.
        :param generator: A function that generates a node and returns its name
        :param name: Name to pass to the generator function
        :param kwargs: Additional keyword arguments to pass to the generator function
        :return: The generated node as a Node instance
        """
        kwargs["name"] = str(name)
        return cls(generator(**kwargs))

    def __new__(cls, node: str):
        obj = super().__new__(cls, node)
        obj._node = node
        return obj

    def __getattr__(self, item: str) -> Plug:
        return Plug(self, item)

    def add_attr(self, name: str, **kwargs) -> Plug:
        plug = Plug(self, name)

        if not cmds.objExists(plug):
            cmds.addAttr(self, longName=name, **kwargs)

        return plug


def is_matrix_value(value: any) -> bool:
    if isinstance(value, OpenMaya.MMatrix):
        return True

    if isinstance(value, Iterable) and len(value) == 16 and all(isinstance(v, (int, float)) for v in value):
        return True

    return False
