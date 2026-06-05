from pathlib import Path

import numpy as np
from maya.api import OpenMaya as om
from maya.api.OpenMayaAnim import MFnSkinCluster

from src.lib.logger import logger

NAME = "name"
INFLUENCES = "influences"
WEIGHTS = "weights"


def _get_dag_path(node: str) -> om.MDagPath:
    sel = om.MSelectionList()
    sel.add(node)
    return sel.getDagPath(0)


def get_skin_cluster(node: str) -> MFnSkinCluster:
    sel = om.MSelectionList()
    sel.add(node)
    return MFnSkinCluster(sel.getDependNode(0))


def serialize(shape: str, skin_cluster: str) -> dict:
    shape_dag = _get_dag_path(shape)
    skc_fn = get_skin_cluster(skin_cluster)

    influences = [
        influence.partialPathName()
        for influence in skc_fn.influenceObjects()
    ]

    weights, _ = skc_fn.getWeights(shape_dag, om.MObject())

    return {
        NAME: skc_fn.name(),
        INFLUENCES: influences,
        WEIGHTS: list(weights),
    }


def deserialize(data: dict, shape: str, skin_cluster: str) -> None:
    shape_dag = _get_dag_path(shape)
    skc_fn = get_skin_cluster(skin_cluster)

    vertex_count = om.MFnMesh(shape_dag).numVertices

    comp_fn = om.MFnSingleIndexedComponent()
    vertex_comp = comp_fn.create(om.MFn.kMeshVertComponent)
    comp_fn.addElements(range(vertex_count))

    skc_fn.setWeights(
        shape_dag,
        vertex_comp,
        om.MIntArray(range(len(data[INFLUENCES]))),
        om.MDoubleArray(data[WEIGHTS]),
        normalize=False,
    )


def save(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        path,
        **{
            NAME: np.asarray(data[NAME]),
            INFLUENCES: np.asarray(data[INFLUENCES], dtype=str),
            WEIGHTS: np.asarray(data[WEIGHTS], dtype=np.float64),
        }
    )

    logger.info(f"Saved to {path.resolve()}")


def load(path: Path) -> dict:
    data = np.load(path)
    print(data.files)

    logger.info(f"Loaded from {path.resolve()}")

    return {
        NAME: data[NAME].item(),
        INFLUENCES: data[INFLUENCES].tolist(),
        WEIGHTS: data[WEIGHTS].tolist(),
    }
