import sys
from typing import List
from pathlib import Path

import config
import utils
import cli
from dir_index import DirIndex
from comparison_manager import ComparisonManager
from merge_builder import MergeBuilder


def index_from_prompt():
    input_dirs = cli.prompt_input_dirs()
    index_from_paths(input_dirs)


def index_from_paths(dir_paths: List[Path]):
    check_dirs_exist(dir_paths)
    print("All target dirs exist, beginning indexing...\n")

    index = DirIndex()
    for path in dir_paths:
        index.index_dir(path, normalize_line_endings=True)
    index.print_trait_indexes_to_file(config.OUTPUT_DIR_PATH)

    comparison_manager = ComparisonManager()
    comparison_manager.add_dir_index(index)
    comparison_manager.write_to_file(config.OUTPUT_DIR_PATH)
    comparison_manager.resolve_all()

    merge_builder = MergeBuilder(
        config.OUTPUT_DIR_PATH / "COMPLETE_MERGES" / "MERGE", comparison_manager
    )
    merge_builder.build_merge()
    merge_builder.write_to_file(config.OUTPUT_DIR_PATH)


# Ensure that the output directories exist
def check_dirs_exist(input_paths: List[Path]):
    # Check that input directories are present
    for path in input_paths:
        print(f"Checking if target dir {path} exists...")
        try:
            utils.ensure_path_exists(path, create_if_missing=False)
        except FileNotFoundError as e:
            print(e)
            sys.exit(0)
