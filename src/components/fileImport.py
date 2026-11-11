from pathlib import Path

from maya import cmds

from src.components._comp_base import Component
from src.lib import version
from src.lib import tree
from src.lib.nodes import Node, DeferredNode
from src.lib.naming import Name
from src.rig.module.deferred_plug import DeferredPlug, MATRIX


class MayaFileImport(Component):

    def __init__(self, name: Name):
        super().__init__(name)
        # --- inputs
        self.version: int = -1
        self.path: Path | None = None
        self.category_name: Name | None = None
        self.parent_node: DeferredNode | None = None

        # storage
        self.root_nodes = []
        self.imported_nodes: list[Node]= []

        self._category_node: Node | None = None

    @property
    def category_node(self) -> Node | None:
        return self._category_node

    @property
    def import_parent_node(self) -> Node | None:
        return self.category_node or self.parent_node

    def prepare(self):
        if self.category_name:
            self._category_node = Node(self.category_name).create("transform")

        if self._category_node and self.parent_node:
            tree.parent(self._category_node, self.parent_node.node)

    def load_files(self):
        file_path = version.get_version_path(self.path, self.version)

        self.imported_nodes = [Node(n.split("|")[-1]) for n in cmds.file(str(file_path), i=True, returnNewNodes=True)]
        self.root_nodes = [n for n in self.imported_nodes if tree.is_root_node(n)]

        if parent_node := self.import_parent_node:
            tree.parent(self.root_nodes, parent_node)


class ModelFileImport(MayaFileImport):
    in_parent_mtx = DeferredPlug("parent_mtx", "input", MATRIX)

    def __init__(self, name: Name):
        super().__init__(name)
        self.meshes = []

    def load_files(self):
        super().load_files()
        imported_shapes = [node for node in self.imported_nodes if node.type == "mesh"]
        self.meshes.extend([tree.get_parent(shape) for shape in imported_shapes])

        # for n in self.root_nodes:
        #     node = Node(n)
        #     node.offsetParentMatrix.connect(self.in_parent_mtx.plug)
