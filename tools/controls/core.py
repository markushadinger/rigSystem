from pathlib import Path

from src.rig.data_manager import JsonDataManager
from src.rig.controls import control, shape
from src.architecture.builder import Builder
from src.lib import naming


def export_component_controls(component: str, export_path: Path) -> None:
    """
    Export controls for a given component.
    :param component: Component name
    :param export_path: Path to export the controls to
    :return: None
    """
    transforms = control.get_all_component_controls(component)
    shapes = [shape.get_shape_node(ctrl) for ctrl in transforms]
    data = {naming.strip_suffix(ctrl): shape.get_shape_data_from_scene(ctrl) for ctrl in shapes}

    manager = JsonDataManager(export_path)
    manager.set(data)
    manager.save()


def export_controls_for_asset(builder: Builder):
    for module in builder.modules:
        export_component_controls(module.name, builder.context.shapes_file_path(module.name))
