from maya import cmds
from maya.api import OpenMaya


def get_assign_order_from_scene(nodes: list[str]) -> list[str]:
    """
    Get the assign order for a given set of nodes. Ensures parents always come before children.
    :param nodes: List of nodes
    :return: List of nodes in assign order
    """

    parent_mapping = {n: (cmds.listRelatives(n, parent=True) or [None])[0] for n in nodes}

    result = []

    # find root nodes
    closed_nodes = {n for n, p in parent_mapping.items() if p not in nodes}
    open_nodes = set(nodes) - closed_nodes
    result.extend(closed_nodes)

    while open_nodes:
        current_nodes = {n for n in open_nodes if parent_mapping[n] in closed_nodes}

        if not current_nodes:
            raise RuntimeError("Cycle detected or invalid hierarchy")

        open_nodes -= current_nodes
        closed_nodes |= current_nodes
        result.extend(current_nodes)

    return result


def match_nodes_to_matrices(data: dict[str, list[float]]):
    """
    Match nodes to data dictionary.
    :param data: Dictionary of data
    :return: Dictionary of matched data
    """

    # Filter out non-existent nodes
    matrix_data = {node: OpenMaya.MMatrix(data[node]) for node in data if cmds.objExists(node)}
    open_nodes = {node for node in matrix_data.keys()}
    closed_nodes = set()

    # pre assign matrix to nodes
    for node in open_nodes:
        cmds.xform(node, worldSpace=True, matrix=matrix_data[node])

    while open_nodes:
        matched_nodes = set()

        # check if they moved
        for node in open_nodes:
            current_mtx = OpenMaya.MMatrix(cmds.xform(node, query=True, worldSpace=True, matrix=True))

            if current_mtx.isEquivalent(matrix_data[node]):
                matched_nodes.add(node)
            else:
                cmds.xform(node, worldSpace=True, matrix=matrix_data[node])

        # Assign matched nodes to closed_nodes
        open_nodes -= matched_nodes
        closed_nodes |= matched_nodes
