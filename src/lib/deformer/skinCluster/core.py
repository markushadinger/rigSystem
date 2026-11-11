import numpy

from dataclasses import dataclass

WEIGHT_TYPE = numpy.float64
POINT_TYPE = numpy.float64


@dataclass
class SkinData:
    weights: numpy.ndarray
    influences: numpy.ndarray
    points: numpy.ndarray
    geo: str


def reorder_weights(
        weights: numpy.ndarray,
        influences: numpy.ndarray,
        master_influences: numpy.ndarray,
) -> numpy.ndarray:
    """
    Reorders the current weights.
    master influences and influences need to be identical, besides the order
    :param weights:
    :param influences:
    :param master_influences:
    :return:
    """
    file_indices = {name: i for i, name in enumerate(influences)}
    order = [file_indices[name] for name in master_influences]

    return weights[:, order]


def match_influences(
        weights: numpy.ndarray,
        influences: numpy.ndarray,
        master_influences: numpy.ndarray,
) -> numpy.ndarray:
    indices = {name: i for i, name in enumerate(influences)}
    matched_weights = numpy.zeros((weights.shape[0], len(master_influences)), dtype=weights.dtype)

    for i, influence in enumerate(master_influences):
        indices = indices.get(influence)

        if indices is not None:
            matched_weights[:, i] = weights[:, indices]

    return matched_weights


def get_used_influences_mask(weights: numpy.ndarray, tol: float = 0.0) -> numpy.ndarray:
    return numpy.any(weights > tol, axis=0)


def get_empty_influence_indices(weights: numpy.ndarray, tol: float = 0.0) -> numpy.ndarray:
    return numpy.flatnonzero(~get_used_influences_mask(weights, tol))


def get_used_influence_indices(weights: numpy.ndarray, tol: float = 0.0) -> numpy.ndarray:
    return numpy.flatnonzero(get_used_influences_mask(weights, tol))


def is_normalized(weights: numpy.ndarray, tol: float = 1e-5) -> bool:
    return numpy.allclose(weights.sum(axis=1), 1.0, atol=tol, rtol=0.0)


def normalize(weights: numpy.ndarray) -> numpy.ndarray:
    if not numpy.issubdtype(weights.dtype, numpy.floating):
        weights = weights.astype(numpy.float64)

    sums = weights.sum(axis=1, keepdims=True)
    return numpy.divide(weights, sums, out=numpy.zeros_like(weights), where=sums != 0)


def remove_empty(
        weights: numpy.ndarray,
        influences: numpy.ndarray,
        tol: float = 0.0
) -> tuple[numpy.ndarray, numpy.ndarray]:
    mask = get_used_influences_mask(weights, tol)
    return weights[:, mask], influences[mask]
