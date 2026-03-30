from maya.api.OpenMaya import MMatrix, MVector, MTransformationMatrix, MSpace, MPoint


def get_point_from_matrix(mtx: MMatrix) -> MPoint:
    return MPoint(MTransformationMatrix(mtx).translation(MSpace.kWorld))


def get_matrix_from_axis(x: MVector, y: MVector, z: MVector, p: MPoint) -> MMatrix:
    data = list(x) + [0] + list(y) + [0] + list(z) + [0] + list(p)
    return MMatrix(data)
