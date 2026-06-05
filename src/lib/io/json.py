import json
from pathlib import Path

from src.lib.logger import logger


def export_json(data: dict, path: Path) -> None:
    """
    Export data to a JSON file.
    :param data: Data to export
    :param path: Path to export to
    :return: None
    """

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path.resolve(), "w") as f:
        json.dump(data, f, indent=4)

    logger.info(f"Exported to {path.resolve()}")


def import_json(path: Path) -> dict:
    """
    Import data from a JSON file.
    :param path: Path to import from
    :return: Data from JSON file
    """

    with open(path.resolve(), "r") as f:
        data = json.load(f)

    logger.info(f"Imported from {path.resolve()}")
    return data
