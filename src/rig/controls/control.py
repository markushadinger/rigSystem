from maya import cmds

from src.lib import tags

CONTROL_TAG = "control"


def get_name(name: str, index: str | None = None, side: str | None = None) -> str:
    return "_".join(filter(None, [name, index, side, "ctrl"]))


def build(name: str) -> str:
    control = cmds.createNode("transform", name=name)
    tags.add_tag(control, CONTROL_TAG)
    return control


def add_shape(control: str, shape: str) -> None:
    cmds.parent(shape, control)


def load_shape(control: str, shape_path: str) -> None:
    shape = cmds.file(shape_path, i=True, returnNewNodes=True)[0]
    add_shape(control, shape)
