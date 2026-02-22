import json
import logging

from pathlib import Path


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

    logging.info(f"Exported to {path.resolve()}")


def import_json(path: Path) -> dict:
    """
    Import data from a JSON file.
    :param path: Path to import from
    :return: Data from JSON file
    """

    with open(path.resolve(), "r") as f:
        data = json.load(f)

    logging.info(f"Imported from {path.resolve()}")
    return data
