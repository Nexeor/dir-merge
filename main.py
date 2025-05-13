import argparse
import sys
from pathlib import Path
from typing import List

import utils
import config
import cli

from log_config import setup_logging
from dir_index import DirIndex

# MODES:
# Run test files
# Run from command line
# Run with REPL


def main():
    setup_logging()
    args = parse_args()
    if args.mode == "test":  # Parse pre-determined dirs
        base_dir = Path(__file__).resolve().parent
        paths = [base_dir / config.TEST_PATH_A, base_dir / config.TEST_PATH_B]
        print("Running test mode on predefined test dirs")
        index_dirs(paths)
    elif args.mode == "repl":  # Ask user for dirs interactively
        index_dirs(cli.prompt_input_dirs())
    elif args.mode == "cli":  # Pull dirs from command line input
        index_dirs(args.dirs)
    else:  # Use default dirs
        base_dir = Path(__file__).resolve().parent
        paths = [(base_dir / config.DEFAULT_PATH_A), (base_dir / config.DEFAULT_PATH_B)]
        index_dirs(paths)


# Ensure that the output directories exist
def setup_dirs(input_paths: List[Path]):
    # Check that input directories are present
    for path in input_paths:
        print(f"Checking if target dir {path} exists...")
        try:
            utils.ensure_path_exists(path, create_if_missing=False)
        except FileNotFoundError as e:
            print(e)
            sys.exit(0)


def parse_args():
    parser = argparse.ArgumentParser()

    parser = argparse.ArgumentParser(description="Directory processing tool")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # Test mode
    parser_test = subparsers.add_parser(
        "test", help="Run with pre-defined test directories"
    )
    # REPL mode
    parser_repl = subparsers.add_parser("repl", help="Run in interactive REPL mode")
    # CLI mode
    parser_cli = subparsers.add_parser(
        "cli", help="Supply directories directly on the command line"
    )
    parser_cli.add_argument("dirs", nargs="+", help="Directories to process")
    # Default mode
    parser_default = subparsers.add_parser(
        "default", help="Run on default dirs set in config"
    )

    return parser.parse_args()


def index_dirs(paths: List[Path]):
    setup_dirs(paths)
    print("All target dirs exist, beginning indexing...\n")

    index = DirIndex("index")
    for path in paths:
        index.index_dir(path, normalize_line_endings=True)
    index.print_trait_indexes_to_file(config.OUTPUT_DIR_PATH)

    index.find_compare()
    index.print_comparison_to_file(config.OUTPUT_DIR_PATH)

    # Everything matches
    index.resolve_matches()

    # Two things match
    index.resolve_diff()  # Same name and path (different content)
    index.resolve_content_name_dup()  # Same name and content (different path)
    index.resolve_content_path_dup()  # Same path and content (different name)

    # One thing matches
    index.resolve_name_dup()  # Same name
    index.resolve_content_dup()  # Same content

    # Nothing matches
    index.resolve_unique()

    index.print_union_to_file(config.OUTPUT_DIR_PATH)


# Compare base_dir and new_dir and identify differences
if __name__ == "__main__":
    main()
