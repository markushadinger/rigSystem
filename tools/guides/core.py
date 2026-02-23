from maya import cmds

from src.rig.context import Context
from src.rig.data_manager import JsonDataManager
from src.lib import guide
from src.architecture.builder import Builder


def export_guides_for_component(component_name: str, context: Context):
    guide_data_manager = JsonDataManager(context.guide_file_path(component_name))
    guide_data = guide.get_guide_data_for_component(component_name)
    print(guide_data)
    guide_data_manager.data.update(guide_data)
    guide_data_manager.save()
    
def export_guides_for_asset(builder:Builder):
    for module in builder.modules:
        export_guides_for_component(module.name, builder.context)