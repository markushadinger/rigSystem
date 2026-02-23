from pathlib import Path

from src.lib.io import version
from src.lib.io import json

import logging

class JsonDataManager:

    def __init__(self, file_path: Path, ver: int = -1):
        self._file_path = file_path
        self._data: dict = {}
        self._version = ver

    def load(self) -> None:
        if not self._file_path.parent.exists():
            logging.warning(f"Guide data directory {self._file_path.parent} does not exist. Skipping load.")
            return
        
        versioned_path = version.get_version_path(self._file_path, self._version)
        self._data = json.import_json(versioned_path)

    def save(self) -> None:
        
        if self.data == {}:
            logging.warning(f"No data to save for {self._file_path}. Skipping save.")
            return
            
        next_version_path = version.get_next_version_path(self._file_path)
        json.export_json(self._data, next_version_path)

    @property
    def data(self) -> dict:
        if not self._data:
            self.load()
        return self._data


