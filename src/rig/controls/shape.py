import dataclasses
import math

from maya import cmds
from maya.api import OpenMaya

from src.lib.nodes import Node

COLOR_RED = (1, 0, 0)
COLOR_GREEN = (0, 1, 0)
COLOR_BLUE = (0, 0, 1)
COLOR_YELLOW = (1, 1, 0)
COLOR_WHITE = (1, 1, 1)
COLOR_PURPLE = (1, 0, 1)
COLOR_ORANGE = (1, 0.5, 0)

SIDE_COLOR = {"r": COLOR_RED, "l": COLOR_BLUE, "c": COLOR_YELLOW}

CIRCLE = [
    (0.0, 0.0, -1.0), (-0.383, 0.0, -0.924), (-0.707, 0.0, -0.707), (-0.924, 0.0, -0.383), (-1.0, -0.0, 0.0),
    (-0.924, -0.0, 0.383), (-0.707, -0.0, 0.707), (-0.383, -0.0, 0.924), (0.0, -0.0, 1.0), (0.383, -0.0, 0.924),
    (0.707, -0.0, 0.707), (0.924, -0.0, 0.383), (1.0, 0.0, -0.0), (0.924, 0.0, -0.383), (0.707, 0.0, -0.707),
    (0.383, 0.0, -0.924), (-0.0, 0.0, -1.0)]

CUBE = [
    (1.0, -1.0, 1.0), (-1.0, -1.0, 1.0), (-1.0, -1.0, -1.0), (1.0, -1.0, -1.0), (1.0, -1.0, 1.0), (1.0, 1.0, 1.0),
    (-1.0, 1.0, 1.0), (-1.0, -1.0, 1.0), (-1.0, 1.0, 1.0), (-1.0, 1.0, -1.0), (-1.0, -1.0, -1.0), (-1.0, 1.0, -1.0),
    (1.0, 1.0, -1.0), (1.0, -1.0, -1.0), (1.0, 1.0, -1.0), (1.0, 1.0, 1.0)]

PYRAMID = [
    (-1.0, -1.0, 1.0), (-1.0, -1.0, -1.0), (0.0, 1.0, 0.0), (1.0, -1.0, -1.0), (1.0, -1.0, 1.0), (0.0, 1.0, 0.0),
    (-1.0, -1.0, 1.0), (1.0, -1.0, 1.0), (1.0, -1.0, -1.0), (-1.0, -1.0, -1.0)]

GEAR = [
    (0.22, 0.0, -0.715), (0.102, 0.0, -1.0), (-0.095, 0.0, -1.0), (-0.215, 0.0, -0.717), (-0.35, 0.0, -0.661),
    (-0.632, 0.0, -0.775), (-0.771, 0.0, -0.637), (-0.659, 0.0, -0.355), (-0.715, 0.0, -0.22), (-1.0, -0.0, -0.102),
    (-1.0, -0.0, 0.095), (-0.717, -0.0, 0.215), (-0.661, -0.0, 0.35), (-0.775, -0.0, 0.632), (-0.637, -0.0, 0.771),
    (-0.355, -0.0, 0.659), (-0.22, -0.0, 0.715), (-0.102, -0.0, 1.0), (0.095, -0.0, 1.0), (0.215, -0.0, 0.717),
    (0.35, -0.0, 0.661), (0.632, -0.0, 0.775), (0.771, -0.0, 0.637), (0.659, -0.0, 0.355), (0.715, -0.0, 0.22),
    (1.0, 0.0, 0.102), (1.0, 0.0, -0.095), (0.717, 0.0, -0.215), (0.661, 0.0, -0.35), (0.775, 0.0, -0.632),
    (0.637, 0.0, -0.771), (0.355, 0.0, -0.659), (0.22, 0.0, -0.715)]

TRIANGLE = [
    (0.0, 0.0, 1.0), (-1.0, 0.0, -1.0), (1.0, 0.0, -1.0), (0.0, 0.0, 1.0)]

QUATER_SPHERE = [
    (-0.0, 0.0, -1.0), (-0.588, 0.0, -0.809), (-0.951, 0.0, -0.309), (-0.951, -0.0, 0.309),
    (-0.588, -0.0, 0.809), (0.0, -0.0, 1.0), (0.0, 0.588, 0.809), (0.0, 0.951, 0.309),
    (-0.0, 0.951, -0.309), (0.0, 0.588, -0.809), (-0.0, 0.0, -1.0)]

DROPLET = [
    (0.0, 0.0, -1.0), (-0.588, 0.0, -0.809), (-0.951, 0.0, -0.309), (-0.951, -0.0, -0.0), (-0.0, -0.0, 1.0),
    (0.951, -0.0, 0.0), (0.951, 0.0, -0.309), (0.588, 0.0, -0.809), (0.0, 0.0, -1.0)]

DEFAULT_SHAPE_DATA = {
    "points": CIRCLE,
    "degree": 1,
    "color": COLOR_WHITE,
}


@dataclasses.dataclass
class ShapeData:
    points: list
    degree: int
    color: list


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


def scale(shape: list[tuple[float, ...]], value: float | list[float]) -> list[tuple[float, ...]]:
    """
    Scale a shape.
    :param shape: Shape to value
    :param value: Scale value
    :return: Scaled shape
    """

    if isinstance(value, (float, int)):
        value = [value, value, value]

    return [(x * value[0], y * value[1], z * value[2]) for x, y, z in shape]


def translate(shape: list[tuple[float, ...]], value: list[float]) -> list[tuple[float, ...]]:
    """
    Scale a shape.
    :param shape: Shape to value
    :param value: Scale value
    :return: Scaled shape
    """

    return [(x + value[0], y + value[1], z + value[2]) for x, y, z in shape]


def rotate(shape: list[tuple[float, ...]], value: list[float]) -> list[tuple[float, ...]]:
    """
    Rotate a shape by degrees
    :param shape:
    :param value:
    :return:
    """
    euler = OpenMaya.MEulerRotation([math.radians(v) for v in value])
    return [tuple(OpenMaya.MVector(p).rotateBy(euler)) for p in shape]


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
        "color": shape_node.overrideColorRGB.value[0]
    }


def create(points: list[tuple[float, ...]], degree: int = 1, color: tuple[float, float, float] = COLOR_WHITE) -> Node:
    """
    Create a shape from a list of points.
    :param color:
    :param points: Points to create shape from
    :param degree: Degree of the curve
    :return: Shape node
    """
    trf = Node.generate(cmds.curve, name="tmp", p=points, d=degree)
    shp = Node(cmds.listRelatives(trf, shapes=True)[0])
    set_color(shp, color)
    return Node(trf)


def assign_shape_to_transform(shape_node: Node, transform_node: Node) -> None:
    """
    Assign a shape to a transform.
    :param shape_node: Shape to assign
    :param transform_node: Transform to assign shape to
    :return: None
    """
    shape = get_shape_node(shape_node)
    cmds.parent(shape, transform_node, r=True, s=True)
    cmds.rename(str(shape), f"{transform_node}Shape")
    cmds.delete(shape_node)
