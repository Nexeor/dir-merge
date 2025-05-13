import filecmp
import difflib

from pathlib import Path
from datetime import datetime
from urllib.parse import quote


# Match given path to a base path and extract the relative path
def get_relative_to_base_path(base_paths, full_path):
    path = Path(full_path)

    for base in base_paths:
        if path.is_relative_to(base):
            return path.relative_to(base)

    raise ValueError(
        f"The path {full_path} is not relative to any of the defined base paths."
    )


# Given two file paths, check if they contain the same content
def check_file_diff(path_a, path_b):
    diff_log = None
    if not filecmp.cmp(path_a, path_b, shallow=False):
        base_content = path_a.read_text().splitlines(keepends=True)
        comp_content = path_b.read_text().splitlines(keepends=True)

        diff_log = list(
            difflib.unified_diff(base_content, comp_content, str(path_a), str(path_b))
        )
    return diff_log


def make_link(path: Path) -> str:
    """
    Converts a pathlib.Path object into a clickable file:// URL link.
    """
    # Resolve the absolute path
    abs_path = path.resolve()

    # Convert to URI-compliant format
    # On Windows, need to add an extra slash: file:///C:/Users/...
    # On POSIX, file:///home/user/...
    if abs_path.is_absolute():
        path_str = abs_path.as_posix()  # Converts backslashes to forward slashes
        return (
            f"file:///{quote(path_str)}"
            if Path().anchor
            else f"file://{quote(path_str)}"
        )
    else:
        raise ValueError("Path must be absolute to create a file link.")


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
