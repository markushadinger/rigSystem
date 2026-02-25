from src.lib import om
from src.lib.nodes import Node

from maya.api import OpenMaya


def get_uv_from_point(surface: Node, point: OpenMaya.MPoint) -> tuple[float, float]:
    """
    Get the UV coordinates from a transform node.
    :param point: The point to get the UV coordinates from.
    :param surface: The surface to get the UV coordinates from.
    """

    sel = OpenMaya.MSelectionList()
    sel.add(surface)
    surface_dag = sel.getDagPath(0)

    nurbs_fn = OpenMaya.MFnNurbsSurface(surface_dag)
    _, u, v = nurbs_fn.closestPoint(point, OpenMaya.MSpace.kWorld)

    return u, v


def get_closest_point(surface: Node, point: OpenMaya.MPoint) -> OpenMaya.MPoint:
    """
    Get the closest point on a surface to a given point.
    :param surface: The surface to get the closest point from.
    :param point: The point to get the closest point to.
    :return: The closest point on the surface to the given point.
    """

    sel = OpenMaya.MSelectionList()
    sel.add(surface)
    surface_dag = sel.getDagPath(0)

    nurbs_fn = OpenMaya.MFnNurbsSurface(surface_dag)
    closest_point, _, _ = nurbs_fn.closestPoint(point, OpenMaya.MSpace.kWorld)

    return closest_point
