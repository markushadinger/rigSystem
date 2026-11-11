from src.components._comp_base import Component
from src.lib import transform
from src.lib.naming import Name
from src.lib.nodes import Node


class MatricesConstraint(Component):

    def __init__(self, name: Name):
        super().__init__(name)
        self.input = self.register_input("input", dt="matrix", multi=True)
        self.nodes: list[Node] = list()

    def build(self):
        super().build()
        for i, node in enumerate(self.nodes):
            transform.matrix_constraint(node, self.input[i])
