from pathlib import Path

from maya import cmds

from src.components._comp_base import Component
from src.lib.nodes import Node
from src.lib.naming import Name
from src.rig.module.deferred_plug import DeferredPlug, MATRIX
from src.lib.deformer.io import skinClusterIo
from src.lib.io import version


class SkinClusterImport(Component):
    in_parent_mtx = DeferredPlug("parent_mtx", "input", MATRIX)

    def __init__(self, name: Name):
        super().__init__(name)
        self.version: int = -1
        self.path: Path = Path()
        self.meshes = []

    def import_deformer(self):
        deformer_path = self.context.asset_path() / "deformer"

        for mesh in self.meshes:
            mesh_path = deformer_path / mesh / "skinCluster" / f"{mesh}.npz"

            if not mesh_path.parent.exists():
                continue

            version_path = version.get_version_path(mesh_path, self.version)
            data = skinClusterIo.load(version_path)

            skc = Node(data[skinClusterIo.NAME])

            if not skc.exists():
                skc = cmds.skinCluster(data[skinClusterIo.INFLUENCES], mesh, toSelectedBones=True, name=skc)[0]

            cmds.dgdirty(allPlugs=True)

            skinClusterIo.deserialize(
                skin_cluster=skc,
                shape=cmds.listRelatives(mesh, c=True, s=True)[0],
                data=data
            )
