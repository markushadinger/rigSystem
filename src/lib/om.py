from maya.api import OpenMaya


def get_dag_path(node: str) -> OpenMaya.MDagPath:
    """
    Return the MDagPath of the given node.
    :return:
    """
    sel = OpenMaya.MSelectionList()
    sel.add(node)
    return sel.getDagPath(0)
