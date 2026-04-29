from src.architecture import builder

from src.components._comp_base import Component
from src.rig.module.deferred_plug import DeferredPlug, MATRIX

from src.components.generator import control

from src.lib.naming import Name


class FkChain(builder.Builder):
    def __init__(self, name: Name):
        super().__init__(name)

        self.indices = []
        self.structure = Component(self.name)
        self.in_mtx = self.structure.add_deferred_plug(DeferredPlug("in_mtx", "input", MATRIX))
        self.out_mtx = self.structure.add_deferred_plug(DeferredPlug("out_mtx", "output", MATRIX, multi=True))
        self.add_module(self.structure)

    def init_submodules(self):
        parent_plug = self.in_mtx
        for i, index in enumerate(self.indices):
            fk = control.ControlGenerator(self.name.replace(index=index))
            fk.external_structure = self.structure
            fk.index = index
            fk.external_structure = self.structure.structure
            fk.in_parent_mtx.connect(parent_plug)
            self.add_module(fk)

            parent_plug = fk.out_world_mtx
            self.out_mtx.connect(fk.out_world_mtx, dst_index=i)
