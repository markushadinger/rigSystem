from pathlib import Path
from dataclasses import dataclass

from maya import cmds

from src.rig.context import Context


@dataclass
class Outputs:
    meshes: list[str] | None = None


class ImportModelComponent:
    def __init__(self, name):
        self.name = name
        self.context: Context | None = None

        self.path = ""

        self.outputs = Outputs()

    @classmethod
    def from_settings(cls, settings: dict):
        instance = cls(settings["name"])
        for key, value in settings.items():
            if not hasattr(instance, key):
                continue
            setattr(instance, key, value)
        return instance

    def prepare(self):
        normed_path = Path(self.path).resolve()
        print(f"Importing model from: {normed_path}")

        new_nodes = cmds.file(str(normed_path), i=True, returnNewNodes=True)
        new_shapes = [node for node in new_nodes if cmds.nodeType(node) == "mesh"]

        self.outputs.meshes = [cmds.listRelatives(shape, parent=True)[0] for shape in new_shapes]
