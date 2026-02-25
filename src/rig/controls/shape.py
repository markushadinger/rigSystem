from maya import cmds

from src.lib.nodes import Node

COLOR_RED = (1, 0, 0)
COLOR_GREEN = (0, 1, 0)
COLOR_BLUE = (0, 0, 1)
COLOR_YELLOW = (1, 1, 0)
COLOR_WHITE = (1, 1, 1)
COLOR_PURPLE = (1, 0, 1)
COLOR_ORANGE = (1, 0.5, 0)

CIRCLE = [(0.0, 0.0, -1.0), (-0.383, 0.0, -0.924), (-0.707, 0.0, -0.707), (-0.924, 0.0, -0.383), (-1.0, -0.0, 0.0),
          (-0.924, -0.0, 0.383), (-0.707, -0.0, 0.707), (-0.383, -0.0, 0.924), (0.0, -0.0, 1.0), (0.383, -0.0, 0.924),
          (0.707, -0.0, 0.707), (0.924, -0.0, 0.383), (1.0, 0.0, -0.0), (0.924, 0.0, -0.383), (0.707, 0.0, -0.707),
          (0.383, 0.0, -0.924), (-0.0, 0.0, -1.0)]


def round_point(p: tuple[float, ...], precision: int = 3) -> tuple[float, ...]:
    """
    Round a point to a given precision.
    :param p: Point to round
    :param precision: Precision to round to
    :return: Rounded point
    """
    return tuple(round(x, precision) for x in p)


def get_shape_node(node_name: Node) -> Node:
    """
    Get the shape node of a curve.
    :param node_name: the name of the node
    :return:
    """
    return Node(cmds.listRelatives(node_name, shapes=True)[0])


def get_points_from_scene(shape_node: Node) -> list[tuple[float, ...]]:
    """
    Get a shape from the scene.
    :param shape_node: Node of the shape
    :return: Shape as a list of points
    """
    return [round_point(p) for p in cmds.getAttr(f"{shape_node}.controlPoints[*]")]


def scale_shape(shape: list[tuple[float, ...]], scale: float) -> list[tuple[float, ...]]:
    """
    Scale a shape.
    :param shape: Shape to scale
    :param scale: Scale factor
    :return: Scaled shape
    """
    return [(x * scale, y * scale, z * scale) for x, y, z in shape]


def set_shape(control: str, shape: list[tuple[float, ...]], degree: int = 1) -> None:
    """
    Set a shape on a transform.
    :param control: Transform to set shape on
    :param shape: Shape to set
    :param degree: Degree of the curve
    :return: None
    """
    trf = cmds.curve(name="tmp", p=shape, d=degree)
    shp = cmds.listRelatives(trf, shapes=True)[0]
    cmds.parent(shp, control, r=True, s=True)
    cmds.rename(shp, f"{control}Shape")
    cmds.delete(trf)


def set_color(shape_node: Node, color: tuple[float, float, float]):
    """
    Set the color of a shape.
    :param shape_node: Shape to set color on
    :param color: Color to set
    :return: None
    """
    shape_node.overrideEnabled.value = 1
    shape_node.overrideRGBColors.value = 1
    shape_node.overrideColorRGB.value = color


def get_shape_data_from_scene(shape_node: Node) -> dict:
    """
    Get shape data from the scene.
    :param shape_node: the shape node to get data from
    :return: Shape data
    """

    return {
        "degree": shape_node.degree.value,
        "points": get_points_from_scene(shape_node),
        "color": shape_node.overrideColorRGB.value
    }


def create(points: list[tuple[float, ...]], degree: int = 1, color: tuple[int, ...] = COLOR_WHITE) -> Node:
    """
    Create a shape from a list of points.
    :param color:
    :param points: Points to create shape from
    :param degree: Degree of the curve
    :return: Shape node
    """
    trf = Node(cmds.curve(name="tmp", p=points, d=degree))
    shp = Node(cmds.listRelatives(trf, shapes=True)[0])
    cmds.rename(shp, f"shape{shp}")
    return Node(shp)
