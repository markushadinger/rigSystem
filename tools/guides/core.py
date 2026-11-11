from src.rig.context import Context
from src.rig.data_manager import JsonDataManager
from src.lib import guide
from src.architecture.builder import Builder

from maya.api.OpenMaya import MVector, MMatrix, MPoint
from maya import cmds


def export_guides_for_component(component_name: str, context: Context):
    guide_data_manager = JsonDataManager(context.guide_file_path(component_name))
    guide_data = guide.get_guide_data_for_component(component_name)
    guide_data_manager.set(guide_data)
    guide_data_manager.save()


def export_guides_for_asset(builder: Builder):
    for module in builder.modules:
        export_guides_for_component(module.name.component_name, builder.context)


def make_chain_planar(joints: list[str]):
    points = [MPoint(cmds.xform(j, query=True, worldSpace=True, translation=True)) for j in joints]
    aim = (points[-1] - points[0]).normal()
    up = -(points[1] - (points[0] + ((points[1] - points[0]) * aim) * aim)).normal()
    side = (aim ^ up).normal()
    global_mtx = MMatrix([
        aim.x, aim.y, aim.z, 0,
        up.x, up.y, up.z, 0,
        side.x, side.y, side.z, 0,
        points[0].x, points[0].y, points[0].z, 1
    ])

    local_pnts = []
    local_side = (side * global_mtx.inverse()).normal()

    for i, _ in enumerate(points):
        p = points[i] * global_mtx.inverse()
        p.z = 0
        local_pnts.append(p)

    local_aims = [(p1 - p0).normal() for p1, p0 in zip(local_pnts[1:], local_pnts)]
    local_aims.append(local_aims[-1])

    for i, jnt in enumerate(joints):
        local_aim = local_aims[i]
        local_up = (local_side ^ aim).normal()
        local_mtx = MMatrix([*list(local_aim), 0, *list(local_up), 0, *list(local_side), 0, *list(local_pnts[i])])
        jnt_mtx = local_mtx * global_mtx

        cmds.xform(jnt, worldSpace=True, matrix=jnt_mtx)
        cmds.xform(jnt, worldSpace=True, scale=(1, 1, 1))
