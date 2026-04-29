from src.lib.nodes import Plug, Node

FLOAT = {"at": "float"}
MATRIX = {"dt": "matrix"}

PLUG_LIST = "_deferred_plug_defs"
PLUG_INSTANCES = "_deferred_plug_instances"

MATRIX_LIST = []


class DeferredPlug:
    def __init__(self, name, direction, settings: dict, multi: bool = False):
        """
        Initialize a deferred plug definition.

        :param name: Name of the attribute.
        :param direction: Direction of the plug ("input" or "output").
        :param settings: Maya attribute creation settings.
        :param multi: Whether the attribute is a multi (array) attribute.
        """
        # definition
        self.name = name
        self.direction = direction
        self.settings = settings
        self.multi = multi

        # runtime state
        self.connections: dict[int | None, ["DeferredPlug", int | None]] = {}
        self.plug: Plug | None = None

        self._identifier = None

    def __set_name__(self, owner, name):
        """
        Register the plug definition on the owning class.

        :param owner: The class that owns this descriptor.
        :param name: The attribute name on the class.
        :return: None
        """
        self._identifier = name

        if not hasattr(owner, PLUG_LIST):
            setattr(owner, PLUG_LIST, {})
        getattr(owner, PLUG_LIST)[name] = self

    def __get__(self, instance, owner):
        """
        Retrieve the instance-specific DeferredPlug.

        :param instance: The instance accessing the attribute.
        :param owner: The class owning the descriptor.
        :return: DeferredPlug instance for this object.
        """
        if instance is None:
            return self

        return getattr(instance, PLUG_INSTANCES)[self._identifier]

    def connect(self, other: "DeferredPlug", src_index=None, dst_index: int | None = None):
        """
        Define a connection between this input plug and another output plug.

        :param other: The source (output) DeferredPlug.
        :param src_index: Index on the source plug (for multi attributes).
        :param dst_index: Index on the destination plug (for multi attributes).
        :return: None
        """

        if not self.multi and dst_index is not None and dst_index > 0:
            raise ValueError(f"{self.name} is not a multi plug")

        self.connections[dst_index] = [other, src_index]

    def build_plug(self, node: Node):
        """
        Create the Maya attribute for this plug on the given node.

        :param node: The Maya node wrapper where the attribute will be added.
        :return: None
        """
        node.add_attr(name=self.name, multi=self.multi, **self.settings)
        self.plug = Plug(node, self.name)

    def build_connection(self):
        """
        Create the actual Maya connection between plugs.

        :return: None
        """

        for dst_index, (src_deferred_plug, src_index) in self.connections.items():
            src_plug = src_deferred_plug.plug if src_index is None else src_deferred_plug.plug[src_index]

            if dst_index is None:
                self.plug.connect(src_plug)
                continue

            self.plug[dst_index].connect(src_plug)


def init_deferred_plugs(component):
    """
    Initialize per-instance DeferredPlug objects from class definitions.

    :param component: The component instance containing plug definitions.
    :return: None
    """
    setattr(component, PLUG_INSTANCES, {})

    if not hasattr(component.__class__, PLUG_LIST):
        return

    for name, plug_def in getattr(component.__class__, PLUG_LIST).items():
        plug = DeferredPlug(
            name=name,
            direction=plug_def.direction,
            settings=dict(plug_def.settings),
            multi=plug_def.multi,
        )

        getattr(component, PLUG_INSTANCES)[name] = plug


def build_deferred_plugs(component):
    """
    Create Maya attributes for all deferred plugs on the component.

    :param component: The component instance containing plugs.
    :return: None
    """
    if not hasattr(component, PLUG_INSTANCES):
        return

    for plug in getattr(component, PLUG_INSTANCES).values():
        node = (
            component.structure.input
            if plug.direction == "input"
            else component.structure.output
        )
        plug.build_plug(node)


def connect_deferred_plugs(component):
    """
    Resolve and create all stored connections between plugs.

    :param component: The component instance containing plugs.
    :return: None
    """
    if not hasattr(component, PLUG_INSTANCES):
        return

    for plug in getattr(component, PLUG_INSTANCES).values():
        plug.build_connection()
