from src.rig.module.deferred_plug import DeferredPlug
from src.rig.module.deferred_plug import build_deferred_plugs
from src.rig.module.deferred_plug import connect_deferred_plugs
from src.rig.context import Context
from src.rig.module import structure


class Component:
    def __init__(self, name):
        self.name = name
        self.context: Context | None = None
        self.structure: structure.ModuleStructure | None = None
        self.inputs: dict[str, DeferredPlug] = {}
        self.outputs: dict[str, DeferredPlug] = {}

        # populate inputs
        for plug_name, plug_type in getattr(self, "INPUTS", {}).items():
            self.inputs[plug_name] = DeferredPlug(plug_name, "input", plug_type)

        # populate outputs
        for plug_name, plug_type in getattr(self, "OUTPUTS", {}).items():
            self.outputs[plug_name] = DeferredPlug(plug_name, "output", plug_type)

    def prepare(self):
        self.structure = structure.build_module_structure(self.name, self.context.rig_root_node)
        build_deferred_plugs(list(self.inputs.values()), self.structure.input)
        build_deferred_plugs(list(self.outputs.values()), self.structure.output)

    def connect(self):
        connect_deferred_plugs(list(self.inputs.values()))
