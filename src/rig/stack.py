from maya import cmds

from src.lib.nodes import Node, Plug
from src.lib import naming

ZERO = "zero"
AUTOMATION = "auto"
SPACESWITCH = "spsw"


class Stack:
    def __init__(self, target: Node):
        """
        Initialize a live stack wrapper.

        :param target: The node at the end of the stack.
        """
        self._target = target
        self._ensure_attr()

    def _ensure_attr(self):
        """
        Ensure the target has a multi message attribute for the stack.
        :return: None
        """
        if not self._target.stack.exists():
            self._target.add_attr("stack", at="message", multi=True, indexMatters=True)

    @property
    def stack(self) -> list[Node]:
        """
        Get ordered stack from target.stack multi attribute.
        :return: Ordered list of stack nodes.
        """
        if not self._target.stack.exists():
            return []

        indices = self._target.stack.connected_indices()

        result = []
        for i in sorted(indices):
            conns: Plug | None = (self._target.stack[i].get_out_connections() or [None])[0]
            if conns:
                result.append(conns.node)

        return result

    def add(self, suffix: str) -> Node:
        """
        Add a new element at the end of the stack.

        :param suffix: Naming suffix for the new node.
        :return: Created Node.
        """
        return self.insert(-1, suffix)

    def insert(self, index: int, suffix: str) -> Node:
        """
        Insert a new element into the stack at a given index.

        :param index: Position to insert at.
        :param suffix: Naming suffix for the new node.
        :return: Created Node.
        """
        stack = self.stack
        length = len(stack)

        index = index if index >= 0 else length + index + 1

        if index < 0:
            raise IndexError(f"Invalid index {index}")

        element = _build_element(self._target, suffix)

        # shift existing connections up
        for i in reversed(range(index, length)):
            src = self._target.stack[i]
            dst = self._target.stack[i + 1]

            conn = src.get_in_connection()
            if conn:
                cmds.disconnectAttr(conn, src)
                cmds.connectAttr(conn, dst)

        # connect new element
        element.stack.connect(self._target.stack[index])

        # parenting logic
        stack = self.stack  # refresh after insertion

        if index > 0:
            cmds.parent(element, stack[index - 1])

        if index < len(stack) - 1:
            cmds.parent(stack[index + 1], element)

        if index == len(stack) - 1:
            cmds.parent(self._target, element)

        return element

    def get_by_index(self, index: int) -> Node:
        return self.stack[index]

    def get_by_suffix(self, suffix: str) -> Node:
        for node in self.stack:
            if node.endswith(suffix):
                return Node(node)


# =========================================================
# BUILD STACK ELEMENT
# =========================================================

def _build_element(target: Node, suffix: str) -> Node:
    """
    Create a new stack node.

    :param target: Target node the stack belongs to.
    :param suffix: Naming suffix for the new node.
    :return: Created Node.
    """
    root_name = naming.strip_suffix(target)
    element_name = naming.get_name(root_name, suffix)

    node = Node.create("transform", name=element_name)

    # match transform
    cmds.xform(node, worldSpace=True, matrix=target.worldMatrix[0].value)

    # add message attr for connection
    node.add_attr("stack", at="message")

    return node
