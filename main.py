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
    elif args.combine:
        build_union()
    else:
        build_union()


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
    dirA = DirIndex("dirA")
    dirA.index_dir(config.PATH_A)
    dirA.index_dir(config.PATH_B)
    dirA.find_compare()
    dirA.print_to_file(config.OUTPUT_DIR_PATH)
    """
    compare = dirA.compare_to(dirB)
    write_compare_to_file(compare)
    """


def build_union():
    setup_logging()
    dirA = DirIndex("dirA")
    dirB = DirIndex("dirB")
    dirA.index_dir(PATH_A)
    dirB.index_dir(PATH_B)

    compare = dirA.compare_to(dirB)
    union = UnionBuilder()
    union.add_matches(compare["MATCH"])


# Compare base_dir and new_dir and identify differences
if __name__ == "__main__":
    main()
