from typing import Callable

from maya import cmds
from maya.api import OpenMaya

from src.components._comp_base import MacroComponent
from src.rig.module.deferred_plug import DeferredPlug, MATRIX
from src.lib import naming
from src.lib.nodes import Node
from src.rig.snippets import surface
from src.rig.snippets import pins


# import numpy


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
        self.uv_smoothing_iterations: int = 100
        self.alpha = 0.3

    def build(self):
        connected_plugs = set(cmds.getAttr(self.in_mtx.plug, multiIndices=True) or [])
        matrix_plugs = [self.in_mtx.plug[i] for i in connected_plugs]

        # build surface
        surface_transform, surface_shape = self._build_ribbon(matrix_plugs)
        self._build_uv_pins(surface_shape)

        pin = self._build_uv_pins(surface_shape)
        self._distribute_uv_pins_even(pin)

    def _build_uv_pins(self, surface_shape: Node):
        """
        create uv pins on the surface
        :param surface_shape:
        :return:
        """
        u_mapping = [i / (self.sample_points - 1) for i in range(self.sample_points)]
        uv_pin_builder = pins.UvPinBuilder()
        uv_pin_builder.pin_name = f"{self.name}_uv_pin"
        uv_pin_builder.surface_shape = surface_shape
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

        return pin

    def _distribute_uv_pins_even(self, pin: Node):
        """
        Iterate over the pin position and smooth their distance till they are even spaced
        :param pin:
        :return:
        """
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
                step = (u_next - u_prev) * error * self.alpha
                new_u = u_curr + step
                pin.coordinate[i].value = [new_u, 0.5]

    def _build_ribbon(self, matrix_plugs) -> tuple[Node, Node]:
        """
        Build the surface
        :param matrix_plugs:
        :return:
        """
        surface_builder = surface.MatrixRibbonBuilder()
        surface_builder.surface_name = self.name.replace(suffix="surf")
        surface_builder.in_matrix_plugs = matrix_plugs
        surface_builder.degree = self.degree
        surface_builder.flip_indices = self.flip_indices
        surface_builder.build()
        cmds.parent(surface_builder.out_surface_transform, self.structure.logic)

        return surface_builder.out_surface_transform, surface_builder.out_surface_shape


class RibbonSkin(Ribbon):
    in_mtx = DeferredPlug("in_mtx", "input", MATRIX, multi=True)
    out_mtx = DeferredPlug("out_mtx", "output", MATRIX, multi=True)
    out_normalized_mtx = DeferredPlug("out_normalized_mtx", "output", MATRIX, multi=True)

    def __init__(self, name: naming.Name):
        super().__init__(name)

        self.u_knot_count: int = 10

    def _build_ribbon(self, matrix_plugs) -> tuple[Node, Node]:
        matrix_values = [p.value for p in matrix_plugs]
        points = surface.get_points(matrix_values, 1, self.flip_indices)

        transform, shape = surface.build_nurbs_surface(
            name=self.name.replace(suffix="surf"),
            knot_u_count=len(matrix_values),
            degree=min(self.degree, len(matrix_plugs) - 1)
        )
        surface.set_points_on_surface(shape, points)
        cmds.parent(transform, self.structure.logic)

        cmds.rebuildSurface(
            shape,
            ch=1,
            rpo=1,
            rebuildType=0,
            endKnots=1,
            keepControlPoints=0,
            keepCorners=1,
            spansU=self.u_knot_count - self.degree,
            degreeU=self.degree,
            spansV=1,
            degreeV=1,
            fitRebuild=0,
            dir=2)

        points = [OpenMaya.MPoint(shape.controlPoints[i].value[0]) for i in range(self.u_knot_count * 2)]

        joints = []
        for i, plug in enumerate(matrix_plugs):
            jnt = Node.create("joint", self.name.replace(index=i, suffix="jnt"))
            jnt.offsetParentMatrix.connect(plug)
            cmds.parent(jnt, self.structure.logic)
            joints.append(jnt)

        skc = cmds.skinCluster(joints, transform, toSelectedBones=True)[0]

        skin_points_based_on_matrix(points, transform, joints, skc, linear)

        return transform, shape


def skin_points_based_on_matrix(
        points: list[OpenMaya.MPoint],
        transform: Node,
        influences: list[Node],
        skin_cluster: str,
        weight_function: Callable[[float], float] | None = None
):
    transform_matrix = OpenMaya.MMatrix(transform.worldMatrix[0].value)
    world_points = [p * transform_matrix for p in points]
    influence_matrices = [OpenMaya.MMatrix(i.worldMatrix[0].value) for i in influences]

    weight_function = weight_function or linear

    weights: list = [(influences[0], 1)] * len(world_points)
    for inf_a, inf_b, jnt_a, jnt_b in zip(influence_matrices, influence_matrices[1:], influences, influences[1:]):
        pnt_a = OpenMaya.MPoint(list(inf_a)[12:])
        pnt_b = OpenMaya.MPoint(list(inf_b)[12:])

        aim = (pnt_b - pnt_a)
        aim_n = aim.normal()

        for i, p in enumerate(world_points):
            local_p = (p - pnt_a) / aim.length()
            value = round((aim_n * local_p), 5)

            if value >= 0:
                weight = weight_function(value)
                weights[i] = ((jnt_a, 1 - weight), (jnt_b, weight))

    for i, w in enumerate(weights):
        cv = f"{transform}.cv[{int(i / 2)}][{i % 2}]"
        cmds.skinPercent(skin_cluster, cv, transformValue=w)


def linear(v: float) -> float:
    return v


def smoothstep(x: float) -> float:
    """
    Classic smoothstep.
    Input/output range: 0..1
    """
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def smootherstep(x: float) -> float:
    """
    Higher-order smoothstep with smoother derivatives.
    Input/output range: 0..1
    """
    x = max(0.0, min(1.0, x))
    return x * x * x * (x * (x * 6.0 - 15.0) + 10.0)