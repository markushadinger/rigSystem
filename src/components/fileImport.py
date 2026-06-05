from pathlib import Path

from maya import cmds

from src.components._comp_base import Component
from src.lib.io import version
from src.lib import tags
from src.lib.nodes import Node
from src.lib.naming import Name
from src.lib import guide
from src.rig.module.deferred_plug import DeferredPlug, MATRIX


class GuideFileImport(Component):

    def __init__(self, name: Name):
        super().__init__(name)
        self.version: int = -1
        self.node = None

    def load_guides(self):
        file_path = version.get_version_path(self.context.asset_path() / "guides" / "guides.ma", self.version)
        new_nodes = cmds.file(str(file_path), i=True, returnNewNodes=True)

        root_nodes = []

        for node in new_nodes:
            if not cmds.objectType(node, isAType="transform"):
                continue

            tags.add_tag(node, guide.GUIDE_TAG)

            if cmds.listRelatives(node, parent=True) is None:
                root_nodes.append(node)

        cmds.parent(root_nodes, self.node)

    def prepare(self):
        self.node = Node.create("transform", name=self.name, parent=self.context.rig_root_node)


class ModelFileImport(Component):
    in_parent_mtx = DeferredPlug("parent_mtx", "input", MATRIX)

    def __init__(self, name: Name):
        super().__init__(name)
        self.version: int = -1
        self.path: Path = Path()
        self.meshes = []
        self.root_nodes = []

    def prepare(self):
        super().prepare()

        file_path = version.get_version_path(self.path, self.version)
        print(f"Importing model from: {file_path}")

        imported_nodes = cmds.file(str(file_path), i=True, returnNewNodes=True)

        imported_shapes = [node for node in imported_nodes if cmds.nodeType(node) == "mesh"]
        imported_transforms = [node for node in imported_nodes if cmds.nodeType(node) == "transform"]

        self.meshes.extend([cmds.listRelatives(shape, parent=True)[0] for shape in imported_shapes])

        self.root_nodes = [n for n in imported_transforms if not cmds.listRelatives(n, parent=True)]

        for n in self.root_nodes:
            node = Node(n)
            node.offsetParentMatrix.connect(self.in_parent_mtx.plug)
