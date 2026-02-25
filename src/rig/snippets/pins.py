from maya import cmds
from maya.api import OpenMaya

from src.lib.nodes import Node, Plug
from src.lib import surface

from enum import Enum


class ConnectionType(Enum):
    OFFSET_PARENT_MATRIX = 0
    DECOMPOSED = 1
    TRANSLATE = 2


def create_orig_shape(shape: Node) -> Node:
    shape = cmds.duplicate(shape, name=f"{shape}Orig")[0]
    return Node(shape)


class UvPinBuilder:
    """
    Build a uv pin node and connect it to a surface.
    """

    def __init__(self):
        self.name: str = "uv_pin"
        self.surface_shape: Node | None = None
        self.out_pin: Node | None = None

    def build(self):
        if not self.surface_shape:
            raise ValueError("Surface shape is not set.")

        og_shape = create_orig_shape(self.surface_shape)

        self.out_pin = Node.create("uvPin", name=f"{self.name}_uvPin")
        self.out_pin.deformedGeometry.connect(self.surface_shape.worldSpace[0])
        self.out_pin.originalGeometry.connect(og_shape.worldSpace[0])


class UvPinTransformDriver:
    """
    Drive transforms with uv pins. Each transform will be driven by the corresponding uv pin.
    """

    def __init__(self):

        self.pin: Node | None = None
        self.uv_values: list[tuple[float, float]] | list[Plug] = []
        self.transforms: list[Node] = []
        self.connection_type: ConnectionType = ConnectionType.OFFSET_PARENT_MATRIX

    def build(self):
        for i, (uv, transform) in enumerate(zip(self.uv_values, self.transforms)):

            if isinstance(uv, Plug):
                self.pin.coordinate[i].connect(uv)
            else:
                self.pin.coordinate[i].value = uv

            match self.connection_type:

                case ConnectionType.OFFSET_PARENT_MATRIX:
                    transform.offsetParentMatrix.connect(self.pin.outputMatrix[i])
                    transform.inheritsTransform.value = 0
                    continue

                case ConnectionType.DECOMPOSED:
                    decomp = Node.create("decomposeMatrix", name=f"{transform}_decomp")
                    self.pin.outputMatrix[i].connect(decomp.inputMatrix)

                    transform.translate.connect(decomp.outputTranslate)
                    transform.rotate.connect(decomp.outputRotate)
                    transform.scale.connect(decomp.outputRotate)
                    transform.inheritsTransform.value = 0
                    continue

                case ConnectionType.TRANSLATE:
                    transform.translate.connect(self.pin.outputTranslate[i])
                    transform.inheritsTransform.value = 0
                    continue
