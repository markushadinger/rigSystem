from pathlib import Path

import numpy
from src.lib.deformer.skinCluster.core import SkinData


def save(path: Path, data: SkinData):
    numpy.savez_compressed(path.resolve(), **data.__dict__)


def load(path: Path) -> SkinData:
    data = numpy.load(path.resolve())
    return SkinData(
        influences=data["influences"],
        weights=data["weights"].reshape(-1, len(data["influences"])),
        points=numpy.zeros(2),
        geo=""
    )
