from src.components._comp_base import Component
from src.lib import naming
from src.rig.module.deferred_plug import FLOAT, DeferredPlug
from src.lib.nodes import Node


class OneMinus(Component):
    in_flt = DeferredPlug("input", "input", FLOAT)
    out_flt = DeferredPlug("input", "output", FLOAT)

    def __init__(self, name: naming.Name):
        super().__init__(name)

    def build(self):
        invert = Node.create("floatMath", self.name.replace(suffix="sub"))
        invert.floatA.value = 1
        invert.floatB.connect(self.in_flt.plug)
        invert.operation.value = 1  # sub

        self.out_flt.plug.connect(invert.outFloat)


class BatchMath(Component):
    in_flt = DeferredPlug("input", "input", FLOAT, multi=True)
    out_flt = DeferredPlug("input", "output", FLOAT)

    node_name = ""
    node_suffix = ""

    def build(self):
        sum_node = Node.create(self.node_name, self.name.replace(suffix=self.node_suffix))
        sum_node.input.connect(self.in_flt.plug)
        self.out_flt.plug.connect(sum_node.output)


class Sum(BatchMath):
    node_name = "sum"
    node_suffix = "sum"


class Mult(BatchMath):
    node_name = "multiply"
    node_suffix = "mlt"


class Average(BatchMath):
    node_name = "average"
    node_suffix = "avg"


class Min(BatchMath):
    node_name = "min"
    node_suffix = "min"


class Max(BatchMath):
    node_name = "max"
    node_suffix = "max"
