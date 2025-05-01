import os
import logging

from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Tuple

import utils
from file import File
from comparison import Comparison, ComparisonResult
from comparison_index import ComparisonIndex


class DirIndex:
    def __init__(self, name, name_index=None, path_index=None, size_index=None):
        self.name = name
        self.logger = logging.getLogger(__name__)

        # Common trait indexes
        self.all_files: List[File] = []
        self.name_index: Dict[str : List[File]] = name_index or defaultdict(list)
        self.path_index: Dict[str : List[File]] = path_index or defaultdict(list)
        self.size_index: Dict[int : List[File]] = size_index or defaultdict(list)

        # Cache for already seen comparisons
        self.comparison_cache: Dict[Tuple(File, File) : Comparison] = defaultdict(list)

        # Comparison indexes
        self.matches = ComparisonIndex("MATCH", ComparisonResult.MATCH)
        self.diffs = ComparisonIndex("DIFF", ComparisonResult.DIFF)
        self.content_name_dups = ComparisonIndex(
            "CONTENT-NAME-DUP", ComparisonResult.CONTENT_NAME_DUP
        )
        self.content_path_dups = ComparisonIndex(
            "CONTENT-PATH-DUP", ComparisonResult.CONTENT_PATH_DUP
        )
        self.name_dups = ComparisonIndex("NAME-DUP", ComparisonResult.NAME_DUP)
        self.content_dups = ComparisonIndex("CONTENT-DUP", ComparisonResult.CONTENT_DUP)
        self.unique: List[File] = []  # List of "unique" files

    def __repr__(self):
        return (
            f"DirIndex(name={self.name!r}, "
            f"files_indexed={len(self.all_files)}, "
            f"unique_files={len(self.unique)}, "
            f"comparisons_cached={len(self.comparison_cache)})"
        )

    def __str__(self):
        return (
            f"DirIndex '{self.name}': "
            f"{len(self.all_files)} files indexed, "
            f"{len(self.unique)} unique, "
            f"{len(self.comparison_cache)} comparisons cached"
        )

    def print_index_to_file(self, output_dir: Path):
        # Gather indexes
        indexes = {
            "NAME_INDEX": self.name_index,
            "PATH_INDEX": self.path_index,
            "SIZE_INDEX": self.size_index,
        }
        for name, index in indexes.items():
            # Generate the string of this index
            msg = [f"{self.name}\n"]
            for key, file_list in index.items():
                msg.append(f"{key}:\n")
                for file in file_list:
                    msg.append(f"\t{str(file)}\n\n")

            # Write the string to the file
            utils.write_to_file(
                filename=name,
                output_dir=output_dir / name,
                msg="".join(msg),
                is_timestamped=True,
            )

    def print_comparison_to_file(self, output_dir: Path):
        """Write comparison indexes and unique files to files in output_dir."""
        # Gather comparison indexes and write to file
        comparison_indexes = [
            self.matches,
            self.diffs,
            self.content_name_dups,
            self.name_dups,
            self.name_dups,
            self.content_dups,
        ]
        for index in comparison_indexes:
            index.print_to_file(output_dir)

        # Gather unique files and write to file
        utils.write_to_file(
            filename="UNIQUE",
            output_dir=output_dir / "UNIQUE",
            msg=str("\n".join(map(str, self.unique))),
            is_timestamped=True,
        )

    # Add all files in the given directory to this index
    def index_dir(self, base_dir_path):
        # Recursively iterate over filetree and add to index
        base_dir_path = Path(base_dir_path)
        for abs_path in base_dir_path.rglob("*"):
            if not utils.is_hidden(abs_path):
                if abs_path.is_file():
                    self.logger.info(
                        f"Indexing file: \n\tName: {abs_path.name}\n\tPath: {abs_path}"
                    )
                    file = File(base_dir_path, abs_path)
                    self.all_files.append(file)
                    self.name_index[file.name].append(file)
                    self.path_index[file.rel_path].append(file)
                    self.size_index[file.size].append(file)
                elif abs_path.is_dir():
                    self.logger.info(f"Indexing directory: {abs_path}")

    # Get list of all files in index
    # Check that file against all files that share a name:
    #   Match, Diff, Content-Name-Dup, Name-Dup
    #   Cache comparisons as we go to not redo the same compare
    # Check that file against all files that share size:
    #   Content-Path-Dup, Content-Dup
    # If no other comparison is found yet, then the file is unique
    def find_compare(self):
        for file in self.all_files:
            file: File
            self.logger.info(f"\nAnalyzing {file}")

            # Test against other files with the same name
            self.logger.info("Comparing against same name:")
            same_name_files = self.name_index[file.name]
            found_name_compare = self._compare_group(same_name_files)
            if not found_name_compare:
                self.logger.info("No same name matches found")

            # Test against other files with the same size
            self.logger.info("Comparing against same size:")
            same_size_files = self.size_index[file.size]
            found_size_compare = self._compare_group(same_size_files)
            if not found_size_compare:
                self.logger.info("No same size matches found")

            if not found_name_compare and not found_size_compare:
                self.logger.info("Unique file")
                self.unique.append(file)

    def _compare_group(self, file_list):
        """Compares all unique pairs in a group. Returns True if any comparison was found within the group."""
        found = False
        if len(file_list) > 1:
            for i, file_a in enumerate(file_list):
                for file_b in file_list[i + 1 :]:
                    if self._compare_files(file_a, file_b):
                        found = True
        return found

    def _compare_files(self, file_a: File, file_b: File):
        """Compares two files and caches the result. Returns True if a meaningful comparison was added."""
        if (
            self.comparison_cache[(file_a, file_b)]
            or self.comparison_cache[(file_b, file_a)]
        ):
            return False

        comparison: Comparison = file_a.compare_to(file_b)
        self.comparison_cache[(file_a, file_b)] = comparison
        match comparison.type:
            case ComparisonResult.MATCH:
                self.matches.add_comparison(comparison)
            case ComparisonResult.DIFF:
                self.diffs.add_comparison(comparison)
            case ComparisonResult.CONTENT_NAME_DUP:
                self.content_name_dups.add_comparison(comparison)
            case ComparisonResult.CONTENT_PATH_DUP:
                self.content_path_dups.add_comparison(comparison)
            case ComparisonResult.NAME_DUP:
                self.name_dups.add_comparison(comparison)
            case ComparisonResult.CONTENT_DUP:
                self.content_dups.add_comparison(comparison)
            case _:
                self.logger.info(f"NO RELATION: {file_a.name}, {file_b.name}")
                return False
        return True
