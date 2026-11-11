from pathlib import Path

from maya import cmds

from src.components._comp_base import Component
from src.lib.nodes import Node
from src.lib.naming import Name
from src.rig.module.deferred_plug import DeferredPlug, MATRIX
from src.lib import version

from src.lib.deformer.skinCluster.io import numpy_io
from src.lib.deformer.skinCluster.io import maya_io


class SkinClusterImport(Component):
    in_parent_mtx = DeferredPlug("parent_mtx", "input", MATRIX)

    def __init__(self, name: Name):
        super().__init__(name)
        self.version: int = -1
        self.path: Path = Path()
        self.meshes = []

    def import_deformer(self):

        for mesh in self.meshes:
            mesh_path = self.path / mesh / "skinCluster" / f"{mesh}.npz"

            if not mesh_path.parent.exists():
                continue

            version_path = version.get_version_path(mesh_path, self.version)
            data = numpy_io.load(version_path)
            # data.geo = mesh
            # data.points = maya_io.get_points_from_mesh(mesh)

            # create missing joints
            for influence in data.influences:
                if cmds.objExists(influence):
                    continue
                Node(influence).create("joint")

            skc = cmds.skinCluster(data.influences.tolist(), mesh, toSelectedBones=True, name=f"{mesh}_skc")[0]
            cmds.dgdirty(allPlugs=True)

            maya_io.set_weights(skc, data.weights)
