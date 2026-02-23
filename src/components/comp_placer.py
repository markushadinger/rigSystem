from dataclasses import dataclass

from maya import cmds

from src.rig.controls import color, control, shape
from src.lib import attributes, tags
from src.components._comp_base import Component
from src.rig.module.deferred_plug import TYPE_MATRIX


@dataclass
class Outputs:
    control: str | None = None
    scale_attr: str | None = None


class PlacerComponent(Component):
    OUTPUTS = {
        "placer_ws": TYPE_MATRIX,
    }

    def build(self):
        ctrl = control.build(self.name)
        tags.add_tag(ctrl, "placer")
        cmds.parent(ctrl, self.structure.controls)

        # Lock and hide all transform attributes
        for attr in attributes.TRANSFORM_ATTRS + (attributes.VISIBILITY_ATTR,):
            attributes.make_unkeyable(ctrl, attr)
        attributes.convert_to_uniform_scale(ctrl)

        # Set shape and color
        shape.set_shape(ctrl, shape.scale_shape(shape.CIRCLE, 50))
        color.set_color(ctrl, color.COLOR_YELLOW)

        self.outputs["placer_ws"].plug << ctrl.worldMatrix[0]
        print(self.outputs["placer_ws"].plug)
