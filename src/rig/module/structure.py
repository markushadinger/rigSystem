from src.lib import naming
from src.lib.nodes import Node


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
            self.root = Node.create("transform", name=name, parent=parent)
            self.guides = Node.create("transform", name=name.replace(suffix="guides"), parent=self.root)
            self.input = Node.create("transform", name=name.replace(suffix="input"), parent=self.root)
            self.logic = Node.create("transform", name=name.replace(suffix="logic"), parent=self.root)
            self.controls = Node.create("transform", name=name.replace(suffix="controls"), parent=self.root)
            self.deform = Node.create("transform", name=name.replace(suffix="deform"), parent=self.root)
            self.output = Node.create("transform", name=name.replace(suffix="output"), parent=self.root)

        else:
            self.root = parent.root
            self.guides = parent.guides
            self.input = Node.create("transform", name=name.replace(suffix="input"), parent=parent.input)
            self.logic = parent.logic
            self.controls = parent.controls
            self.deform = parent.deform
            self.output = Node.create("transform", name=name.replace(suffix="output"), parent=parent.output)

        for group in [
            self.root,
            self.guides,
            self.output,
            self.input,
            self.controls,
            self.logic,
            self.deform,
        ]:
            for attr in "trs":
                for axis in "xyz":
                    attribute = attr + axis
                    getattr(group, attribute).lock = True
                    getattr(group, attribute).k = False
                    getattr(group, attribute).cb = False

            group.inheritsTransform.value = False
