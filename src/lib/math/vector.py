from maya.api.OpenMaya import MPoint, MVector


def get_normal_from_triangle(a: MPoint, b: MPoint, c: MPoint) -> MVector:
    ab = b - a
    ac = c - a
    return (ac ^ ab).normalize()
