from maya import cmds

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


def get_shape_from_scene(shape_name: str) -> list[tuple[float, ...]]:
    """
    Get a shape from the scene.
    :param shape_name: Name of the shape
    :return: Shape as a list of points
    """
    shape = cmds.listRelatives(shape_name, shapes=True)[0]
    return [round_point(p) for p in cmds.getAttr(f"{shape}.controlPoints[*]")]


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
