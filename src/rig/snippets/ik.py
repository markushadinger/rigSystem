from maya import cmds

from src.lib import naming
from src.lib.nodes import Node
from src.lib.nodes import Plug


class SimpleBuilder:
    def __init__(self, name: str):
        self.name: str = name
        self.init_matrices: list = []

        self.in_target_vector: Plug | None = None
        self.in_start_vector: Plug | None = None

        self.out_joints: list[Node] | None = None

    def build(self):
        for i, mtx in enumerate(self.init_matrices):
            jnt = Node.create("joint", naming.get_name(self.name, index=i, suffix="jnt"))
            cmds.xform()
