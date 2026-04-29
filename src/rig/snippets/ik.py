from maya import cmds
from maya.api.OpenMaya import MMatrix

from src.lib import naming
from src.lib.nodes import Node
from src.lib.nodes import Plug
from src.lib.math import matrix


def get_pole_vector_matrix(am: MMatrix, bm: MMatrix, cm: MMatrix, distance: float) -> MMatrix:
    """
    returns the matrix of the pole vector
    :param am:
    :param bm:
    :param cm:
    :param distance:
    :return:
    """
    a = matrix.get_point_from_matrix(am)
    b = matrix.get_point_from_matrix(bm)
    c = matrix.get_point_from_matrix(cm)

    aim = (c - a).normalize()
    aim_center = a + ((b - a) * aim) * aim
    side = (b - aim_center).normalize()
    up = aim ^ side
    return matrix.get_matrix_from_axis(aim, side, up, b + side * distance)


def build_pole_ik(
        name: naming.Name,
        chain: list[Node],
        driver_plug: Plug,
        pole_plug: Plug,
        maintain_offset: bool = False
) -> (Node, Node):
    """

    :param name:
    :param chain:
    :param driver_plug:
    :param pole_plug:
    :param maintain_offset:
    :return: ik_handle, pole_constraint
    """
    if maintain_offset:
        driver_mtx = MMatrix(driver_plug.value)
        end_mtx = MMatrix(chain[-1].worldMatrix[0].value)
        offset_mtx = end_mtx * driver_mtx.inverse()

        mlt_node = Node.create("multMatrix", str(name.replace(suffix="mmlt", extra=f"{name.extra}_offset")))
        mlt_node.matrixIn[0].value = offset_mtx
        mlt_node.matrixIn[1].connect(driver_plug)
        driver_plug = mlt_node.matrixSum

    ik_handle, _ = cmds.ikHandle(
        name=str(name.replace(suffix="ikh")),
        startJoint=chain[0],
        endEffector=chain[-1],
        solver="ikRPsolver"
    )
    ik_handle = Node(ik_handle)
    ik_handle.offsetParentMatrix.connect(driver_plug)
    cmds.xform(ik_handle, worldSpace=True, matrix=chain[-1].worldMatrix[0].value)

    pole_const = Node.create("poleVectorConstraint", str(name.replace(suffix="pvc")))
    pole_const.target[0].targetParentMatrix.connect(pole_plug)
    pole_const.pivotSpace.connect(chain[0].parentMatrix[0])
    pole_const.constraintRotatePivot.connect(chain[0].t)
    pole_const.constraintParentInverseMatrix.connect(ik_handle.parentInverseMatrix[0])

    ik_handle.poleVector.connect(pole_const.constraintTranslate)

    return ik_handle, pole_const


class SimpleBuilder:
    def __init__(self, name: str):
        self.name: str = name
        self.init_matrices: list = []

        self.in_target_vector: Plug | None = None
        self.in_start_vector: Plug | None = None
        self.out_joints: list[Node] | None = None

    def build(self):
        for i, mtx in enumerate(self.init_matrices):
            jnt = Node.create("joint", naming.get_name(self.name, index=i, suffix="jnt"))
            cmds.xform()
