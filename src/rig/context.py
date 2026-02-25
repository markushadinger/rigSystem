from pathlib import Path

from src.lib.nodes import Node


class Context:
    def __init__(self, name: str, project_path: str, asset_type: str):
        self.name = name
        self.project_path = Path(project_path)  # convert once
        self.asset_type = asset_type
        self.rig_root_node = Node | None

    def asset_path(self) -> Path:
        return self.project_path / self.asset_type / self.name

    def component_path(self, module_name: str) -> Path:
        return self.asset_path() / "modules" / module_name

    def guide_path(self, module_name: str) -> Path:
        return self.component_path(module_name) / "guides"

    def guide_file_path(self, module_name: str) -> Path:
        return self.guide_path(module_name) / "guides.json"

    def shapes_path(self, module_name: str) -> Path:
        return self.component_path(module_name) / "shapes"

    def shapes_file_path(self, module_name: str) -> Path:
        return self.shapes_path(module_name) / "controls.json"
