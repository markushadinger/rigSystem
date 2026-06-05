from src.architecture import builder

from src.components._comp_base import Component
from src.rig.module.deferred_plug import DeferredPlug, MATRIX, BOOL

from src.components.control import ControlGenerator

from src.lib.naming import Name


class FkChain(builder.Builder):
    def __init__(self, name: Name):
        super().__init__(name)

        self.default_shape = None
        self.indices_without_shape = []
        self.indices = []

        self.fk_modules: list[ControlGenerator] = []

        self.structure = Component(self.name)
        self.in_mtx = self.structure.add_deferred_plug(DeferredPlug("in_mtx", "input", MATRIX))
        self.in_visibility = self.structure.add_deferred_plug(DeferredPlug("in_visibility", "input", BOOL))
        self.out_mtx = self.structure.add_deferred_plug(DeferredPlug("out_mtx", "output", MATRIX, multi=True))
        self.out_normalized_mtx = self.structure.add_deferred_plug(
            DeferredPlug("out_norm_mtx", "output", MATRIX, multi=True))
        self.add_module(self.structure)

    def init_submodules(self):
        parent_plug = self.in_mtx
        for i, index in enumerate(self.indices):
            fk = ControlGenerator(self.name.replace(index=index))
            fk.external_structure = self.structure
            fk.default_shape = self.default_shape
            fk.index = index
            fk.has_shape = index not in self.indices_without_shape
            fk.external_structure = self.structure.structure
            fk.in_parent_mtx.connect(parent_plug)
            fk.in_visibility.connect(self.in_visibility)
            self.add_module(fk)
            self.fk_modules.append(fk)

            parent_plug = fk.out_normalized_mtx
            self.out_mtx.connect(fk.out_world_mtx, dst_index=i)
            self.out_normalized_mtx.connect(fk.out_normalized_mtx, dst_index=i)
