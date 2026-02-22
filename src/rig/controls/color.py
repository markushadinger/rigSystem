from maya import cmds

COLOR_RED = (1, 0, 0)
COLOR_GREEN = (0, 1, 0)
COLOR_BLUE = (0, 0, 1)
COLOR_YELLOW = (1, 1, 0)
COLOR_WHITE = (1, 1, 1)
COLOR_PURPLE = (1, 0, 1)
COLOR_ORANGE = (1, 0.5, 0)


def set_color(shape: str, color: tuple[float, float, float]) -> None:
    cmds.setAttr(f"{shape}.overrideEnabled", 1)
    cmds.setAttr(f"{shape}.overrideRGBColors", 1)
    cmds.setAttr(f"{shape}.overrideColorRGB", *color)
