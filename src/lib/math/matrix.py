from maya.api.OpenMaya import MMatrix, MVector, MTransformationMatrix, MSpace, MPoint


def get_point_from_matrix(mtx: MMatrix) -> MPoint:
    return MPoint(MTransformationMatrix(mtx).translation(MSpace.kWorld))


def get_matrix_from_axis(x: MVector, y: MVector, z: MVector, p: MPoint) -> MMatrix:
    data = list(x) + [0] + list(y) + [0] + list(z) + [0] + list(p)
    return MMatrix(data)


from maya.api.OpenMaya import MMatrix, MVector, MPoint


def get_matrix_from_aim_up_pos(
        aim_vector: MVector,
        up_vector: MVector,
        pos: MPoint,
        up_axis: str,
        aim_axis: str
) -> MMatrix:
    aim_vector = aim_vector.normal()
    up_vector = up_vector.normal()

    side_vector = (aim_vector ^ up_vector).normal()
    up_vector = (side_vector ^ aim_vector).normal()

    aim_row = "xyz".index(aim_axis.lower())
    up_row = "xyz".index(up_axis.lower())
    side_row = ({0, 1, 2} - {aim_row, up_row}).pop()

    rows = [None, None, None]

    rows[aim_row] = aim_vector
    rows[up_row] = up_vector
    rows[side_row] = side_vector

    return MMatrix([
        [rows[0].x, rows[0].y, rows[0].z, 0.0],
        [rows[1].x, rows[1].y, rows[1].z, 0.0],
        [rows[2].x, rows[2].y, rows[2].z, 0.0],
        [pos.x, pos.y, pos.z, 1.0],
    ])
