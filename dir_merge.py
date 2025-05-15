import argparse
from pathlib import Path

from dir_merge_runner import index_from_args, index_from_prompt
from log_config import setup_logging


def main():
    """
    Parse the command-line arguments and call the appropriate indexing function.

    If directory paths are provided as arguments, index those directories.
    Otherwise, prompt the user interactively to input directories for indexing.
    """
    setup_logging()
    args = parse_args()
    if not args.dirs:
        index_from_prompt()
    else:
        index_from_args(args.dirs)


def parse_args():
    """
    Parse command-line arguments for the DirMerge program.

    Returns:
        argparse.Namespace: An object containing the parsed command-line arguments.
            - dirs (list of str): List of directory paths provided by the user.
              May be empty if no directories were specified.
    """
    parser = argparse.ArgumentParser(
        prog="DirMerge", description="Compare and merge several directories"
    )
    parser.add_argument("dirs", nargs="*", type=Path, help="Directories to be merged")

    return parser.parse_args()


if __name__ == "__main__":
    main()
