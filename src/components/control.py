import dataclasses

from maya import cmds

from src.components._comp_base import MacroComponent
from src.lib.naming import Name
from src.lib.nodes import Node
from src.rig.controls import shape
from src.rig.stack import Stack, ZERO
from src.rig.controls import control
from src.rig.module.deferred_plug import DeferredPlug, MATRIX
from src.lib import guide
from src.components.offset_systems import OffsetSystem


class ControlGenerator(MacroComponent):
    in_parent_mtx = DeferredPlug("in_parent_mtx", "input", MATRIX)
    out_local_mtx = DeferredPlug("out_local_mtx", "output", MATRIX)
    out_struct_mtx = DeferredPlug("out_struct_mtx", "output", MATRIX)
    out_world_mtx = DeferredPlug("out_world_mtx", "output", MATRIX)
    out_normalized_mtx = DeferredPlug("out_norm_mtx", "output", MATRIX)

    def __init__(self, name: Name):
        super().__init__(name)

        self.default_shape: shape.ShapeData | None = None
        self.has_shape: bool = True
        self.index: str | None = None
        self.control: Node | None = None
        self.stack: Stack | None = None
        self._control_deferred_plugs: list[DeferredPlug] = []
        self._offset_system: OffsetSystem | None = None
        self._disabled_attributes: set[str] = set('v')

    def add_attr(self, name: str, **kwargs) -> DeferredPlug:
        plug = DeferredPlug(name, "output", kwargs)
        self._control_deferred_plugs.append(plug)
        return plug

    def add_seperator(self, label: str):
        ctrl_count = len(self._control_deferred_plugs)
        self._control_deferred_plugs.append(dict(
            name=f"sep_{ctrl_count}",
            nn="------",
            at="enum",
            en=label,
            k=True,
        ))

    def remove_attr(self, attr: str):
        self._disabled_attributes.add(attr)

    def set_offset_system(self, system: OffsetSystem):
        self._offset_system = system

    def prepare(self):
        super().prepare()

        for plug in self._control_deferred_plugs:
            if isinstance(plug, DeferredPlug):
                plug.build_plug(self.structure.output)

    def build(self):
        shape_data = self.shape_data.get(self.name.replace(index=self.index),
                                         dataclasses.asdict(self.default_shape) if self.default_shape else None)
        matrix_data = guide.get_world_matrix(self.name.replace(index=self.index))

        self.control = control.build(self.name)
        if self.has_shape:
            control.add_shape_from_dict(self.control, shape_data)
        cmds.xform(self.control, worldSpace=True, matrix=matrix_data)

        self.stack = Stack(self.control)
        zero = self.stack.add(ZERO)
        cmds.parent(zero, self.structure.controls)

        zero.offsetParentMatrix.connect(self.in_parent_mtx.plug)

        if self._offset_system:
            self._offset_system.build(self.control)

        self._build_custom_attributes()
        self._remove_attributes()

        struct_mmlt = Node.create("multMatrix", name=self.name.replace(suffix="mmlt"))
        struct_mmlt.matrixIn[0].connect(self.control.worldMatrix[0])
        struct_mmlt.matrixIn[1].connect(zero.worldInverseMatrix[0])

        self.out_local_mtx.plug.connect(self.control.matrix)
        self.out_struct_mtx.plug.connect(struct_mmlt.matrixSum)
        self.out_world_mtx.plug.connect(self.control.worldMatrix[0])
        self.out_normalized_mtx.plug.connect(control.get_normalized_matrix_output(self.control))

    def _build_custom_attributes(self):
        """

        :return:
        """
        for deferred_plug in self._control_deferred_plugs:
            if isinstance(deferred_plug, DeferredPlug):
                new_attr = self.control.add_attr(deferred_plug.name, **deferred_plug.settings)
                deferred_plug.plug.connect(new_attr)
            else:
                self.control.add_attr(**deferred_plug)

    def _remove_attributes(self):
        for attr in self._disabled_attributes:
            plug = getattr(self.control, attr)
            plug.lock = True
            plug.k = False
            plug.cb = False

