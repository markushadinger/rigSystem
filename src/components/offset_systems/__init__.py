from typing import Protocol

from src.lib.nodes import Node


class OffsetSystem(Protocol):

    def build(self, node: Node):
        ...
