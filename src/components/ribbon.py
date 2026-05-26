from maya import cmds
from maya.api import OpenMaya

from src.components._comp_base import MacroComponent
from src.rig.module.deferred_plug import DeferredPlug, MATRIX
from src.lib import naming
from src.lib.nodes import Node
from src.rig.snippets import surface
from src.rig.snippets import pins


class Ribbon(MacroComponent):
    in_mtx = DeferredPlug("in_mtx", "input", MATRIX, multi=True)
    out_mtx = DeferredPlug("out_mtx", "output", MATRIX, multi=True)
    out_normalized_mtx = DeferredPlug("out_normalized_mtx", "output", MATRIX, multi=True)

    def __init__(self, name: naming.Name):
        super().__init__(name)

        self.sample_points: int = 10
        self.degree: int = 3
        self.flip_indices: list[int] = []
        self.normal_axis = "z"
        self.tangent_axis = "y"
        self.uv_smoothing_iterations:int = 100

    def build(self):
        connected_plugs = set(cmds.getAttr(self.in_mtx.plug, multiIndices=True) or [])
        matrix_plugs = [self.in_mtx.plug[i] for i in connected_plugs]
        u_mapping = [i / (self.sample_points - 1) for i in range(self.sample_points)]

        # build surface
        surface_builder = surface.MatrixRibbonBuilder()
        surface_builder.surface_name = self.name.replace(suffix="surf")
        surface_builder.in_matrix_plugs = matrix_plugs
        surface_builder.degree = 4
        surface_builder.flip_indices = self.flip_indices
        surface_builder.build()
        cmds.parent(surface_builder.out_surface_transform, self.structure.logic)

        uv_pin_builder = pins.UvPinBuilder()
        uv_pin_builder.pin_name = f"{self.name}_uv_pin"
        uv_pin_builder.surface_shape = surface_builder.out_surface_shape
        uv_pin_builder.build()

        pin = uv_pin_builder.out_pin

        pin.normalAxis.value = "xzy".index(self.normal_axis)
        pin.tangentAxis.value = "xzy".index(self.tangent_axis)

        for i, u in enumerate(u_mapping):
            pin.coordinate[i].value = [u, 0.5]

            self.out_mtx.plug[i].connect(pin.outputMatrix[i])

            mlt = Node.create("multMatrix", name=self.name.replace(index=i, suffix="norm_mmlt"))
            mlt.matrixIn[0].value = OpenMaya.MMatrix(pin.outputMatrix[i].value).inverse()
            mlt.matrixIn[1].connect(pin.outputMatrix[i])
            self.out_normalized_mtx.plug[i].connect(mlt.matrixSum)

        alpha = 0.3

        # distribute even
        for _iter in range(self.uv_smoothing_iterations):
            points = [OpenMaya.MPoint(pin.outputMatrix[i].value[12:-1]) for i in range(self.sample_points)]
            distances = [p1.distanceTo(p2) for p1, p2 in zip(points[:-1], points[1:])]
            current_us = [pin.coordinate[i].value[0][0] for i in range(self.sample_points)]

            for i in range(1, self.sample_points - 1):
                u_prev = current_us[i - 1]
                u_curr = current_us[i]
                u_next = current_us[i + 1]

                d_left = distances[i - 1]
                d_right = distances[i]
                denom = d_left + d_right

                if denom < 1e-8:
                    continue

                error = (d_right - d_left) / denom
                step = (u_next - u_prev) * error * alpha
                new_u = u_curr + step
                pin.coordinate[i].value = [new_u, 0.5]
