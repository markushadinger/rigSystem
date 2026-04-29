from maya import cmds

from maya import cmds

from src.components._comp_base import MacroComponent
from src.rig.data_manager import GuideDataManager
from src.lib import guide
from src.lib import hierarchy
from src.lib import naming


class GuideImport(MacroComponent):
    def __init__(self, name: naming.Name):
        super().__init__(name)
        self.component_name: naming.Name | None = None
        self.version: int = -1
        self.guide_data = GuideDataManager(self.name, guide.DEFAULT_VALUE)

    def load_guide_data(self):
        component = self.component_name or self.name.component_name
        self.guide_data.load_if_empty(self.context.guide_file_path(component), self.version)

    def build_guides(self):
        parent = self.structure.guides

        # Build spine joints
        for i in self.indices:
            jnt_node = guide.create_guide_joint(i.replace(extra=None))
            cmds.parent(jnt_node, parent)
            parent = jnt_node

        # assign guide data to joints
        guide_data_dict = {naming.get_name(n, suffix=guide.SUFFIX): m for n, m in self.guide_data.data.items()}
        hierarchy.match_nodes_to_matrices(guide_data_dict)

    @property
    def indices(self) -> list[naming.Name]:
        return self.guide_data.indices

    @indices.setter
    def indices(self, value):
        self.guide_data.indices = value
