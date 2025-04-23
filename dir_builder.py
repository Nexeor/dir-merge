# Duplicates: Choose which duplicates to keep and which to get rid of
# Match/DNE: Copy over
# Diff: Choose which version to keep

# 1) Combine MATCH with DNE and use them to generate base dir
# 2) For each DUP, choose which paths to keep
# 3) For each DIFF, choose which version to keep

import sys
import os
import logging
import shutil

from typing import Dict, List
from datetime import datetime
from pathlib import Path

import utils

BASE_ROOT_PATH = (
    r"C:\Users\trjji\Documents\Coding Projects\obsidian-helpers\combined\test"
)


class UnionBuilder:
    def __init__(self):
        root_path = self.__setup_root()
        self.union_path = root_path

    def add_matches(self, match_index: Dict[str, List[str]]):
        for _, abs_paths in match_index.items():
            # Generate relative paths
            rel_paths = []
            for path in abs_paths:
                rel_paths.append(utils.get_relative_to_base_path(path))

            # User decides what path to keep
            rel_path, abs_path = self.__gather_match_input(rel_paths, abs_paths)

            # Print and log chosen match
            match_msg = self.__get_match_msg(rel_paths, abs_paths)
            chosen_msg = f"Chosen path: {rel_path}\n\t{abs_path}"
            print(chosen_msg)
            logging.info(match_msg)
            logging.info(chosen_msg)

            # Copy file from selected path
            output_path = Path(self.union_path / rel_path)
            os.makedirs(output_path.parent, exist_ok=True)
            print(abs_path, output_path)
            shutil.copy2(Path(abs_path), Path(output_path))

    def __gather_match_input(self, rel_paths, abs_paths):
        while True:
            print(self.__get_match_msg(rel_paths, abs_paths))
            try:
                user_input = int(input("Input # of path to keep: "))
                if 0 <= user_input < len(rel_paths):
                    return rel_paths[user_input], abs_paths[user_input]
                else:
                    raise ValueError(
                        f"Invalid selection: {user_input}. Must be between 0 and {len(abs_paths) - 1}"
                    )
            except ValueError as e:
                print(
                    f"Error: {e}. Please enter an integer between {0} - {len(rel_paths) - 1}"
                )

    @staticmethod
    def __get_match_msg(rel_paths, abs_paths):
        msg = "MATCH: Choose path to keep:\n"
        for i, (rel_path, abs_path) in enumerate(zip(rel_paths, abs_paths)):
            msg += f"\t{i}) {rel_path}\n"
            msg += f"\t\tLink: {utils.make_link(abs_path)}\n"
        return msg

    # Given the root_path, create it if it doesn't already exist
    def __setup_root(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        root = Path(f"{BASE_ROOT_PATH}-{timestamp}")

        if root.exists():
            msg = f"Aborting build: root directory {root} already exists"
            print(msg)
            logging.error(msg)
            sys.exit(1)

        try:
            root.mkdir(parents=True)
            logging.info(f"Created root dir at: {root}")
        except Exception as e:
            msg = f"Failed to create root directory due to {e}"
            print(msg)
            logging.exception(msg)
            sys.exit(1)

        return root
