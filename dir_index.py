import os
import logging

from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Tuple

import utils
import cli
from file import File
from comparison import Comparison, ComparisonResult
from comparison_index import ComparisonIndex


class DirIndex:
    def __init__(self, name, name_index=None, size_index=None):
        self.name = name
        self.logger = logging.getLogger(__name__)
        self.base_dir_paths = []

        # Common trait indexes
        self.file_list: List[File] = []
        self.name_index: Dict[str : List[File]] = name_index or defaultdict(list)
        self.size_index: Dict[int : List[File]] = size_index or defaultdict(list)

        # Cache for already seen comparisons
        self.comparison_cache: Dict[Tuple(File, File) : Comparison] = defaultdict(list)

        # Union index { rel_path : File }
        self.union: Dict[Path : List[File]] = defaultdict(list)

    def __repr__(self):
        return (
            f"DirIndex(name={self.name!r}, "
            f"files_indexed={len(self.file_list)}, "
            f"unique_files={len(self.unique)}, "
            f"comparisons_cached={len(self.comparison_cache)})"
        )

    def __str__(self):
        return (
            f"DirIndex '{self.name}': "
            f"{len(self.file_list)} files indexed, "
            f"{len(self.unique)} unique, "
            f"{len(self.comparison_cache)} comparisons cached"
        )

    def print_trait_indexes_to_file(self, output_dir: Path):
        # Gather indexes
        indexes = {
            "NAME_INDEX": self.name_index,
            "SIZE_INDEX": self.size_index,
        }
        for name, index in indexes.items():
            self._print_index_to_file(name, index, output_dir)

    def print_union_to_file(self, output_dir: Path):
        self._print_index_to_file("UNION", self.union, output_dir)

    def _print_index_to_file(self, index_name: str, index: Dict, output_dir: Path):
        # Generate the string of this index
        msg = [f"{self.name}\n"]
        for key, file_list in index.items():
            msg.append(f"{key}:\n")
            for file in file_list:
                msg.append(f"\t{str(file)}\n\n")

            # Write the string to the file
            utils.write_to_file(
                filename=index_name,
                output_dir=output_dir / index_name,
                msg="".join(msg),
                is_timestamped=True,
            )

    # Add all files in the given directory to this index
    def index_dir(self, base_dir_path, normalize_line_endings=False):
        # Recursively iterate over filetree and add to index
        base_dir_path = Path(base_dir_path)
        self.base_dir_paths.append(base_dir_path)
        for abs_path in base_dir_path.rglob("*"):
            if not utils.is_hidden(abs_path):
                if abs_path.is_file():
                    self.logger.info(
                        f"Indexing file: \n\tName: {abs_path.name}\n\tPath: {abs_path}"
                    )

                    # Convert to lf for diff comparison
                    if abs_path.suffix.lower() == ".md" and normalize_line_endings:
                        self.logger.info(f"Normalizing line endings to lf...")
                        self._convert_to_lf(abs_path)

                    # Create file object and add to indexes
                    file = File(base_dir_path, abs_path)
                    self.file_list.append(file)
                    self.name_index[file.name].append(file)
                    self.size_index[file.size].append(file)
                elif abs_path.is_dir():
                    self.logger.info(f"Indexing directory: {abs_path}")

    def _convert_to_lf(self, file_path):
        """MODIFIES FILE CONTENT!"""
        with open(file_path, "r", newline="", encoding="utf-8") as file:
            content = file.read()

        # Replace all line endings with LF (Unix-style)
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        with open(file_path, "w", newline="", encoding="utf-8") as file:
            file.write(content)
