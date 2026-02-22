from maya import cmds

from src.rig.context import Context
from src.rig.nodes.nodes import Node


class PrepSceneComponent:
    def __init__(self, name):
        self.name = name
        self.context: Context | None = None

    def prepare(self):
        cmds.file(new=True, force=True)

        self.context.rig_root_node = Node(cmds.createNode("transform", name=f"rig"))
