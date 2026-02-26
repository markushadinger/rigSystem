def get_name(component: str, side: str = None, index: int = None, extra: str = None, suffix: str = None) -> str:
    """
    Get the name of the component. The name is used to identify the component and is used in the guide data.
    """
    parts = [component, side, extra, index, suffix]
    filtered_parts = [str(part) for part in parts if part is not None]
    return "_".join(filtered_parts)


def strip_suffix(name: str) -> str:
    """
    Strip the suffix from the name.
    :param name: Name to strip suffix from
    :return: Name without suffix
    """

    if "_" in name:
        return name.rsplit("_", 1)[0]

    return name
