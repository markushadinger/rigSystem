from pathlib import Path
import logging

from src.lib.io import version
from src.lib.io import json


class JsonDataManager():

    def __init__(self, file_path: Path, ver: int = -1, default=None):
        self._file_path = file_path
        self._data: dict = {}
        self._version = ver
        self._default = default

    def load(self) -> None:
        if not self._file_path.parent.exists():
            logging.warning(f"Data directory {self._file_path.parent} does not exist. Skipping load.")
            return

        versioned_path = version.get_version_path(self._file_path, self._version)
        self._data = json.import_json(versioned_path)

    def save(self) -> None:

        if self._data == {}:
            logging.warning(f"No data to save for {self._file_path}. Skipping save.")
            return

        next_version_path = version.get_next_version_path(self._file_path)
        json.export_json(self._data, next_version_path)

    def set(self, data: dict) -> None:
        self._data = data

    def load_if_empty(self) -> None:
        if not self._data:
            self.load()

    def get(self, index, default=None):
        return self._data.get(str(index), default if default is not None else self._default)

    @property
    def data(self) -> dict:
        self.load_if_empty()
        return self._data
