from maya import cmds

from src.lib.nodes import Node
from src.components._comp_base import Component


class PrepSceneComponent(Component):
    def __init__(self, name):
        super().__init__(name, None)

    def prepare(self):      
        cmds.file(new=True, force=True)
        self.context.rig_root_node = Node(cmds.createNode("transform", name=f"rig"))
