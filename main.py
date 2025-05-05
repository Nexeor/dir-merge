import argparse
import sys
from pathlib import Path
from typing import List

import utils
import config

from log_config import setup_logging
from dir_index import DirIndex
from union_builder import UnionBuilder


def main():
    setup_dirs()
    setup_logging()
    args = parse_args()
    if args.index:
        build_index()


# Ensure that the output directories exist
def setup_dirs():
    input_paths: List[Path] = [
        config.PATH_A,
        config.PATH_B,
    ]

    # Check that input directories are present
    for path in input_paths:
        print(path)
        try:
            utils.ensure_path_exists(path, create_if_missing=False)
        except FileNotFoundError as e:
            print(e)
            sys.exit(0)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--index", action="store_true")
    parser.add_argument("-u", "--union", action="store_true")

    return parser.parse_args()


def build_index():
    # setup_logging()
    test_index = DirIndex("test_index")
    test_index.index_dir(config.PATH_A)
    test_index.index_dir(config.PATH_B)
    test_index.print_trait_indexes_to_file(config.OUTPUT_DIR_PATH)

    test_index.find_compare()
    test_index.print_comparison_to_file(config.OUTPUT_DIR_PATH)

    # test_index.resolve_matches()
    test_index.resolve_diff()
    test_index.print_union_to_file(config.OUTPUT_DIR_PATH)


# Compare base_dir and new_dir and identify differences
if __name__ == "__main__":
    main()
