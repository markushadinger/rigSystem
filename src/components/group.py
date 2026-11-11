from src.components._comp_base import Component
from src.lib import tree
from src.lib.naming import Name
from src.lib.nodes import DeferredNode, Node


class Group(Component):

    def __init__(self, name:Name):
        super().__init__(name)
        self.node: DeferredNode = DeferredNode()
        self.parent: DeferredNode | None = None

    def prepare(self):
        self.node.node = Node(self.name).create("transform")
        if self.parent and self.parent.node:
            tree.parent(self.node.node, self.parent.node)
