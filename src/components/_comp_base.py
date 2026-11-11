from src.lib.nodes import Node, Plug
from src.rig.module.deferred_plug import DeferredPlug
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

LOGIC_GRP = "logic"
CONTROL_GRP = "controls"


class Component:
    def __init__(self, name: Name):
        init_deferred_plugs(self)
        self.name: Name = name
        self.component_node: Node | None = None
        self._input: Node = Node(str(self.name.replace(suffix="input")))
        self._output: Node = Node(str(self.name.replace(suffix="output")))
        self._input_plugs: list[tuple[Plug, dict]] = list()
        self._output_plugs: list[tuple[Plug, dict]] = list()

        self.context: Context | None = None
        self.structure: structure.ModuleStructure = structure.ModuleStructure()
        self.external_structure: structure.ModuleStructure | None = None

    def register_input(self, name, **settings) -> Plug:
        plug = Plug(self._input, name)
        self._input_plugs.append((plug, settings))
        return plug

    def register_output(self, name, **settings) -> Plug:
        plug = Plug(self._output, name)
        self._output_plugs.append((plug, settings))
        return plug

    def build_sort_group(self, name:str):
        if not self.component_node:
            self.component_node = Node.create()

    def prepare(self):
        # build input and output node
        self._input.create("simpleTestNode")
        self._output.create("simpleTestNode")

        for plug, settings in self._input_plugs:
            self._input.add_attribute(plug.name, **settings)

        for plug, settings in self._output_plugs:
            self._output.add_attribute(plug.name, **settings)

    def connect(self):
        for plug, _ in self._input_plugs:
            plug.resolve_deferred()

    def add_deferred_plug(self, plug: DeferredPlug) -> DeferredPlug:
        getattr(self, PLUG_INSTANCES)[plug.name] = plug
        return plug

    def build(self):
        # clean up hooks before using them

        for this_plug, _ in self._input_plugs:
            other_plug = this_plug.get_in_connection()

            if this_plug.is_multi() and other_plug.is_multi():
                this_plug.disconnect_in()

                for i in other_plug.connected_indices():
                    this_plug[i].connect(other_plug[i])


class MacroComponent(Component):
    pass
