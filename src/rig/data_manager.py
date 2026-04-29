from pathlib import Path
import logging

from maya.api import OpenMaya

from src.lib.io import version as version_lib
from src.lib.io import json
from src.lib.naming import Name


class JsonDataManager:

    def __init__(self, default):
        self._data: dict = {}
        self._default = default

    def load(self, file_path: Path, version: int = -1) -> None:
        if not file_path.parent.exists():
            logging.warning(f"Data directory {file_path.parent} does not exist. Skipping load.")
            return

        versioned_path = version_lib.get_version_path(file_path, version)
        self._data = json.import_json(versioned_path)

    def save(self, file_path: Path) -> None:

        if self._data == {}:
            logging.warning(f"No data to save for {file_path}. Skipping save.")
            return

        next_version_path = version_lib.get_next_version_path(file_path)
        json.export_json(self._data, next_version_path)

    def set(self, data: dict) -> None:
        self._data = data

    def load_if_empty(self, file_path: Path, version: int = -1) -> None:
        if not self._data:
            self.load(file_path, version)

    def get(self, index, default=None):
        return self._data.get(str(index), default if default is not None else self._default)

    @property
    def data(self) -> dict:
        return self._data


class GuideDataManager(JsonDataManager):
    def __init__(self, component: Name, default):
        super().__init__(default)
        self.name = component
        self._indices: list[str] | None = None
        self._matrices: list[OpenMaya.MMatrix] | None = None

    @property
    def indices(self):
        return self._indices

    @indices.setter
    def indices(self, value: list[str]):
        self._indices = [self.name.replace(index=i, extra=None) for i in value]

    @property
    def matrices(self) -> list[OpenMaya.MMatrix]:
        if not self._matrices:
            self._matrices = [OpenMaya.MMatrix(self.get(i)) for i in self._indices]
        return self._matrices
