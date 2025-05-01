import filecmp
import difflib

from pathlib import Path
from datetime import datetime
from urllib.parse import quote
from typing import Dict

from config import PATH_A, PATH_B, OUTPUT_DIR_PATH


# Match given path to a base path and extract the relative path
def get_relative_to_base_path(full_path):
    path = Path(full_path)

    for base in [PATH_A, PATH_B]:
        if path.is_relative_to(base):
            return path.relative_to(base)

    raise ValueError(
        f"The path {full_path} is not relative to any of the defined base paths."
    )


# Given two file paths, check if they contain the same content
def check_file_diff(file_path_A, file_path_B):
    diff_log = None
    if not filecmp.cmp(file_path_A, file_path_B, shallow=False):
        with open(file_path_A) as base:
            base_content = base.readlines()
        with open(file_path_B) as comp:
            comp_content = comp.readlines()

        diff_log = list(
            difflib.unified_diff(base_content, comp_content, file_path_A, file_path_B)
        )
    return diff_log


def make_link(path):
    encoded_path = quote(path.replace("\\", "/"))
    return f"file:///{encoded_path}"


def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


# Returns True if any part of the given path is a hidden file (prefixed with '.')
def is_hidden(path: Path):
    for elem in path.parts:
        if elem[0] == ".":
            return True
    return False


def write_to_file(filename: str, output_dir: Path, msg: str, is_timestamped=False):
    """
    Writes a message to a text file in the specified output directory.

    If `is_timestamped` is True, appends a timestamp to the filename before writing.
    Creates the output directory if it does not already exist.

    Args:
        filename (str): The base name of the file (without extension or timestamp).
        output_dir (Path): The directory where the file should be saved.
        msg (str): The message content to be written to the file.
        is_timestamped (bool, optional): Whether to append a timestamp to the filename. Defaults to False.

    Returns:
        None
    """
    if is_timestamped:
        filename = f"{filename}-{get_timestamp()}.txt"
    else:
        filename = f"{filename}.txt"

    output_path = output_dir / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    with open(output_path, "w", encoding="utf-8") as output_file:
        output_file.write(msg)


# Check if the provided path exists. If it does, return it.
# If build is true, create the dir if it doesn't exist
# Otherwise, raise FnF exception
def ensure_path_exists(path: Path, create_if_missing=True):
    if path.exists():
        return path
    if create_if_missing:
        path.mkdir(parents=True, exist_ok=True)
        return path
    else:
        raise FileNotFoundError(f"Path does not exist: {path}")
