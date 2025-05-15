import sys
from typing import List
from pathlib import Path

import config
import utils
from dir_index import DirIndex


def index_from_prompt():
    return 0


def index_from_args(dir_paths: List[Path]):
    setup_dirs(dir_paths)
    print("All target dirs exist, beginning indexing...\n")

    index = DirIndex("index")
    for path in dir_paths:
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
