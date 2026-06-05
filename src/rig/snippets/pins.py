from enum import Enum

from maya import cmds

from src.lib.nodes import Node, Plug


class ConnectionType(Enum):
    OFFSET_PARENT_MATRIX = 0
    DECOMPOSED = 1
    TRANSLATE = 2


def get_orig_shape_plug(shape: Node) -> Plug:
    create_plug = Plug(shape, "create")
    in_plug = create_plug.get_in_connection()

    if in_plug:
        return in_plug

    return Plug.from_string(cmds.deformableShape(shape, createOriginalGeometry=True)[0])


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

        orig_plug = get_orig_shape_plug(self.surface_shape)

        self.out_pin = Node.create("uvPin", name=f"{self.name}_uvPin")
        self.out_pin.deformedGeometry.connect(self.surface_shape.worldSpace[0])
        self.out_pin.originalGeometry.connect(orig_plug)


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
