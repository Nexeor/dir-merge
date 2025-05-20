import logging
import sys
import shutil
import os

from collections import defaultdict
from pathlib import Path
from typing import List, Dict

import utils
from file import File
from comparison_manager import ComparisonManager
from comparison_index import ComparisonIndex


class MergeBuilder:
    def __init__(self, comparison_manager: ComparisonManager):
        self.merge: Dict[Path : List[File]] = defaultdict(list)
        self.comparison_manager = comparison_manager
        self.build_merge()

    def __str__(self):
        msg = [f"Merge:\n"]
        for path, file_list in self.merge.items():
            msg.append(f"{path}:\n")
            for file in file_list:
                msg.append(f"\t{str(file)}\n\n")
        return "".join(msg)

    def write_to_file(self, output_path: Path):
        utils.write_to_file(
            "MERGE", output_path / "MERGE", str(self), is_timestamped=True
        )

    def _setup_root(self, target_dir):
        root_path = Path(f"{target_dir}-{utils.get_timestamp()}")
        logging.info(f"Setting up root at {root_path}")

        if root_path.exists():
            msg = f"Aborting build: root directory {root_path} already exists"
            print(msg)
            logging.error(msg)
            sys.exit(1)
        try:
            root_path.mkdir(parents=True)
            logging.info(f"Created root dir at: {root_path}")
        except Exception as e:
            msg = f"Failed to create root directory due to {e}"
            print(msg)
            logging.exception(msg)
            sys.exit(1)

        return root_path

    def build_merge(self):
        for comparison_index in self.comparison_manager.comparisons.values():
            comparison_index: ComparisonIndex
            for file_list in comparison_index.index.values():
                if type(file_list) == list:
                    for file in file_list:
                        file: File
                        output_path = Path(file.dir_path)
                        self.merge[output_path].append(file)

    def write_merge_to_disk(self, output_dir):
        root_path = self._setup_root(output_dir)
        for path, file_list in self.merge.items():
            for file in file_list:
                file: File
                output_path = Path(root_path / file.rel_path)
                os.makedirs(output_path.parent, exist_ok=True)
                shutil.copy2(Path(file.abs_path), Path(output_path))
