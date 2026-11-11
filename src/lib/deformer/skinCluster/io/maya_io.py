import numpy
from maya.api import OpenMaya
from maya.api.OpenMayaAnim import MFnSkinCluster
from maya import cmds

from src.lib.deformer.skinCluster.core import SkinData


def to_skc_fn(skin_cluster: str) -> MFnSkinCluster:
    sel = OpenMaya.MSelectionList()
    sel.add(skin_cluster)
    return MFnSkinCluster(sel.getDependNode(0))


def to_dag_path(dag: str) -> OpenMaya.MDagPath:
    sel = OpenMaya.MSelectionList()
    sel.add(dag)
    return sel.getDagPath(0)


def get_geometry(skin_cluster: str) -> str:
    return cmds.skinCluster(skin_cluster, q=True, g=True)[0]


def get_mesh_components(mesh: str):
    mesh_fn = OpenMaya.MFnMesh(to_dag_path(mesh))
    comp_fn = OpenMaya.MFnSingleIndexedComponent()

    vertex_comp = comp_fn.create(OpenMaya.MFn.kMeshVertComponent)
    comp_fn.addElements(range(mesh_fn.numVertices))
    return vertex_comp


def get_weights(skin_cluster: str) -> numpy.ndarray:
    skc = to_skc_fn(skin_cluster)
    geo = get_geometry(skin_cluster)
    weights, influence_count = skc.getWeights(to_dag_path(geo), OpenMaya.MObject())
    np_weights = numpy.asarray(weights, dtype=numpy.float64)
    return numpy.reshape(np_weights, (-1, influence_count))


def set_weights(skin_cluster: str, weights: numpy.ndarray):
    skc = to_skc_fn(skin_cluster)
    geo = get_geometry(skin_cluster)
    components = get_mesh_components(geo)

    skc.setWeights(
        to_dag_path(geo),
        components,
        OpenMaya.MIntArray(numpy.arange((weights.shape[1]))),
        OpenMaya.MDoubleArray(weights.flatten().tolist()),
        False,
    )


def get_influences(skin_cluster: str) -> numpy.ndarray:
    skc = to_skc_fn(skin_cluster)
    return [inf.partialPathName() for inf in skc.influenceObjects()]


def get_points_from_mesh(mesh: str) -> numpy.ndarray:
    mesh = OpenMaya.MFnMesh(to_dag_path(mesh))
    points = numpy.asarray(mesh.getPoints(), dtype=numpy.float64).reshape(-1, 4)
    return numpy.delete(points, [3], axis=1)


def load(skin_cluster: str) -> SkinData:
    geo = get_geometry(skin_cluster)

    return SkinData(
        weights=get_weights(skin_cluster),
        influences=get_influences(skin_cluster),
        geo=geo,
        points=get_points_from_mesh(geo)
    )
