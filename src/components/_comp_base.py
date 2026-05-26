from src.rig.module.deferred_plug import DeferredPlug
from src.rig.module.deferred_plug import build_deferred_plugs
from src.rig.module.deferred_plug import connect_deferred_plugs
from src.rig.module.deferred_plug import init_deferred_plugs
from src.rig.module.deferred_plug import PLUG_INSTANCES
from src.rig.context import Context
from src.rig.module import structure
from src.lib.naming import Name

from src.rig.data_manager import GuideDataManager
from src.rig.data_manager import JsonDataManager
from src.lib import guide
from src.lib import naming
from src.rig.controls import shape


class Component:
    def __init__(self, name):
        init_deferred_plugs(self)
        self.name: Name = name
        self.context: Context | None = None
        self.structure: structure.ModuleStructure = structure.ModuleStructure()
        self.external_structure: structure.ModuleStructure | None = None

    def prepare(self):
        parent = self.external_structure or self.context.rig_root_node
        self.structure.build(self.name, parent)
        build_deferred_plugs(self)

    def connect(self):
        connect_deferred_plugs(self)

    def add_deferred_plug(self, plug: DeferredPlug) -> DeferredPlug:
        getattr(self, PLUG_INSTANCES)[plug.name] = plug
        return plug

    def cleanup(self):
        for plug in getattr(self, PLUG_INSTANCES).values():
            if plug.direction != "input":
                continue

            if not plug.multi:
                continue

            out_indices = plug.plug.connected_indices()
            in_plug = plug.plug.get_in_connection()

            try:
                for i in out_indices:
                    plug.plug[i].connect(in_plug[i])
            except:
                pass


class MacroComponent(Component):

    def __init__(self, name):
        super().__init__(name)

        self.guide_version: int = -1
        self.guide_data: GuideDataManager | None = GuideDataManager(self.name, guide.DEFAULT_VALUE)
        self.shape_data: JsonDataManager | None = JsonDataManager(shape.DEFAULT_SHAPE_DATA)
        self.filtered_indices: list[str] | None = None

    @property
    def local_indices(self) -> list[naming.Name]:
        if not self.filtered_indices:
            return self.guide_data.indices
        return [self.name.replace(index=i) for i in self.filtered_indices]

    def load_build_data(self):
        self.shape_data.load_if_empty(self.context.shapes_file_path(self.name.component_name))
