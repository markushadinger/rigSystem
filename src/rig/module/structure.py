from src.lib import naming
from src.lib.nodes import Node

from src.lib import constants


class ModuleStructure:
    def __init__(self):
        self.root: Node | None = None
        self.guides: Node | None = None
        self.input: Node | None = None
        self.logic: Node | None = None
        self.controls: Node | None = None
        self.deform: Node | None = None
        self.output: Node | None = None

    def build(self, name: naming.Name, parent: Node | None = None):
        """
        Build module structure.

        :param name: Module name
        :param parent: Parent node or ModuleStructure
        :return: None
        """

        is_module_parent = isinstance(parent, ModuleStructure)

        if not is_module_parent:
            self.root = Node(name).create("transform", parent=parent)
            # self.guides = Node(name.replace(suffix="guides")).create("transform", parent=self.root)
            self.input = Node(name.replace(suffix="input")).create("transform", parent=self.root)
            self.logic = Node(name.replace(suffix="logic")).create("transform", parent=self.root)
            self.controls = Node(name.replace(suffix="controls")).create("transform", parent=self.root)
            self.deform = Node(name.replace(suffix="deform")).create("transform", parent=self.root)
            self.output = Node(name.replace(suffix="output")).create("transform", parent=self.root)

        else:
            self.root = parent.root
            # self.guides = parent.guides
            self.input = Node(name.replace(suffix="input")).create("transform", parent=parent.input)
            self.logic = parent.logic
            self.controls = parent.controls
            self.deform = parent.deform
            self.output = Node(name.replace(suffix="output")).create("transform", parent=parent.output)

        for group in [
            self.root,
            # self.guides,
            self.output,
            self.input,
            self.controls,
            self.logic,
            self.deform,
        ]:
            for attr in constants.ATTR_TRF:
                plug = getattr(group, attr)
                plug.lock = True
                plug.k = False
                plug.cb = False

            group.inheritsTransform.value = False
