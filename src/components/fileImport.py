from maya import cmds

from src.components._comp_base import Component
from src.lib.io import version
from src.lib import tags
from src.lib.nodes import Node
from src.lib.naming import Name
from src.lib import guide


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
