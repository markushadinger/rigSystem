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
    
    if not file_path.parent.exists():
        raise FileExistsError(f"file {file_path} does not exist")
    
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
    versions = get_versions(file_path)
    next_version = versions[-1] + 1 if versions else 0
    return file_path.parent / construct_file_name(file_path.name, next_version)

{
"leg_l_upperTwist_0_skn":"leg_l_upper0_skn",
"leg_l_upperTwist_1_skn":"leg_l_upper1_skn",
"leg_l_upperTwist_2_skn":"leg_l_upper2_skn",
"leg_l_upperTwist_3_skn":"leg_l_upper3_skn",
"leg_l_upperTwist_4_skn":"leg_l_upper4_skn",

"leg_l_lowerTwist_0_skn":"leg_l_lower0_skn",
"leg_l_lowerTwist_1_skn":"leg_l_lower1_skn",
"leg_l_lowerTwist_2_skn":"leg_l_lower2_skn",
"leg_l_lowerTwist_3_skn":"leg_l_lower3_skn",
"leg_l_lowerTwist_4_skn":"leg_l_lower4_skn",

"leg_r_upperTwist_0_skn":"leg_r_upper0_skn",
"leg_r_upperTwist_1_skn":"leg_r_upper1_skn",
"leg_r_upperTwist_2_skn":"leg_r_upper2_skn",
"leg_r_upperTwist_3_skn":"leg_r_upper3_skn",
"leg_r_upperTwist_4_skn":"leg_r_upper4_skn",

"leg_r_lowerTwist_0_skn":"leg_r_lower0_skn",
"leg_r_lowerTwist_1_skn":"leg_r_lower1_skn",
"leg_r_lowerTwist_2_skn":"leg_r_lower2_skn",
"leg_r_lowerTwist_3_skn":"leg_r_lower3_skn",
"leg_r_lowerTwist_4_skn":"leg_r_lower4_skn",

"arm_l_upperTwist_0_skn":"arm_l_upper0_skn",
"arm_l_upperTwist_1_skn":"arm_l_upper1_skn",
"arm_l_upperTwist_2_skn":"arm_l_upper2_skn",
"arm_l_upperTwist_3_skn":"arm_l_upper3_skn",
"arm_l_upperTwist_4_skn":"arm_l_upper4_skn",

"arm_l_lowerTwist_0_skn":"arm_l_lower0_skn",
"arm_l_lowerTwist_1_skn":"arm_l_lower1_skn",
"arm_l_lowerTwist_2_skn":"arm_l_lower2_skn",
"arm_l_lowerTwist_3_skn":"arm_l_lower3_skn",
"arm_l_lowerTwist_4_skn":"arm_l_lower4_skn",

"arm_r_upperTwist_0_skn":"arm_r_upper0_skn",
"arm_r_upperTwist_1_skn":"arm_r_upper1_skn",
"arm_r_upperTwist_2_skn":"arm_r_upper2_skn",
"arm_r_upperTwist_3_skn":"arm_r_upper3_skn",
"arm_r_upperTwist_4_skn":"arm_r_upper4_skn",

"arm_r_lowerTwist_0_skn":"arm_r_lower0_skn",
"arm_r_lowerTwist_1_skn":"arm_r_lower1_skn",
"arm_r_lowerTwist_2_skn":"arm_r_lower2_skn",
"arm_r_lowerTwist_3_skn":"arm_r_lower3_skn",
"arm_r_lowerTwist_4_skn":"arm_r_lower4_skn",

"clavicle_l_skn":"clavicle_l_0_skn",
"clavicle_r_skn":"clavicle_r_0_skn",

"neck_c_twist_0_skn": "neck_c_twist0_skn",
"neck_c_twist_1_skn": "neck_c_twist1_skn",
"neck_c_twist_2_skn": "neck_c_twist2_skn",
"neck_c_twist_3_skn": "neck_c_twist3_skn",
"neck_c_twist_4_skn": "neck_c_twist4_skn",
}