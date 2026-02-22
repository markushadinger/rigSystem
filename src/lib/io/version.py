from pathlib import Path


def construct_file_name(file_name: str, version: int) -> str:
    """
    Construct a file name with a version.
    :param file_name: File name without extension
    :param version: Version number
    :return: File name with version
    """
    file_name, file_type = file_name.split(".")
    return f"{file_name}.{version:04}.{file_type}"


def is_version_file_of(this: str, other: str) -> bool:
    """
    Check if two file names are version files of each other.
    :param this: First file name
    :param other: Second file name
    :return: True if they are version files of each other, False otherwise
    """
    other_name, other_version, other_type = other.split(".")
    this_name, this_type = this.split(".")
    return other_name == this_name and other_type == this_type


def get_version_from_file(file_name: Path) -> int:
    """
    Get the version number from a file name.
    :param file_name: File name
    :return: Version number
    """
    return int(file_name.stem.split(".")[1])


def get_version_files(file_path: Path) -> list[Path]:
    """
    Get all version files for a given file path.
    :param file_path: File path
    :return: List of version file names
    """
    return [f for f in file_path.parent.iterdir() if is_version_file_of(file_path.name, f.name)]


def get_versions(file_path: Path) -> list[int]:
    """
    Get all versions for a given file path.
    :param file_path: File path
    :return: List of versions
    """
    version_files = get_version_files(file_path)
    return sorted([get_version_from_file(f) for f in version_files])


def get_version_path(file_path: Path, version: int = -1) -> Path:
    """
    Get the path for a given version of a file.
    :param file_path: File path
    :param version: Version number
    :return: Path for the given version
    """
    version_files = get_version_files(file_path)
    return file_path.parent / version_files[version]


def get_next_version_path(file_path: Path) -> Path:
    """
    Get the path for the next version of a file.
    :param file_path: File path
    :return: Path for the next version
    """
    next_version = get_versions(file_path)[-1] + 1
    return file_path.parent / construct_file_name(file_path.name, next_version)
