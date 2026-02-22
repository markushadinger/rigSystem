from maya import cmds

from src.rig.nodes.nodes import Plug, Node

TYPE_FLOAT = "float"
TYPE_BOOL = "bool"
TYPE_MATRIX = "matrix"
TYPE_VECTOR3 = "float3"
TYPE_VECTOR2 = "float2"
TYPE_STRING = "string"

mapping = {
    TYPE_FLOAT: {"at": "float"},
    TYPE_BOOL: {"at": "bool"},
    TYPE_MATRIX: {"dt": "matrix"},
    TYPE_VECTOR3: {"at": "float3"},
    TYPE_VECTOR2: {"at": "float2"},
    TYPE_STRING: {"dt": "string"},
}


class DeferredPlug:
    def __init__(self, name, direction, attr_type=TYPE_FLOAT):
        self.name = name
        self.connection: DeferredPlug | None = None
        self.direction = direction  # "input" or "output"
        self.attr_type = attr_type
        self.plug: Plug | None = None

    def __lshift__(self, other):
        # input << output
        if self.direction != "input":
            raise ValueError("Can only assign to input plugs")

        if other.direction != "output":
            raise ValueError("Can only connect from output plugs")

        self.connection = other
        return self

    def build(self, node: Node):
        cmds.addAttr(str(node), longName=self.name, **mapping[self.attr_type])
        self.plug = Plug(node, self.name)

    def connect(self):
        self.plug << self.connection.plug


def build_deferred_plugs(plugs: list[DeferredPlug], node: Node):
    """
    Build deferred plugs.
    :param plugs:
    :param node:
    :return:
    """
    for plug in plugs:
        plug.build(node)


def connect_deferred_plugs(plugs: list[DeferredPlug]):
    """
    Connect deferred plugs.
    :param plugs:
    :return:
    """
    for plug in plugs:
        if plug.connection:
            plug.connect()
