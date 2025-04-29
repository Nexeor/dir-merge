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

        # Dicts for indexing
        self.all_files: List[File] = []
        self.name_index: Dict[str : List[File]] = name_index or defaultdict(list)
        self.path_index: Dict[str : List[File]] = path_index or defaultdict(list)
        self.size_index: Dict[int : List[File]] = size_index or defaultdict(list)

        # Dicts for comparisons
        # Cache for already seen comparisons
        self.comparison_cache: Dict[Tuple(File, File) : Comparison] = defaultdict(
            list
        )
        self.matches = ComparisonIndex("MATCH", ComparisonResult.MATCH)
        self.diffs = ComparisonIndex("DIFF", ComparisonResult.DIFF)
        self.content_name_dups = ComparisonIndex("CONTENT-NAME-DUP", ComparisonResult.CONTENT_NAME_DUP)
        self.content_path_dups = ComparisonIndex("CONTENT-PATH-DUP", ComparisonResult.CONTENT_PATH_DUP)
        self.name_dups = ComparisonIndex("NAME-DUP", ComparisonResult.NAME_DUP)
        self.content_dups = ComparisonIndex("CONTENT-DUP", ComparisonResult.CONTENT_DUP)
        self.unique: List[File] = [] # List of "unique" files

    def __str__(self):
        msg = [f"Index: {self.name}\n"]
        for file_name in self.index:
            msg.append(f"{file_name}\n")
            for file_path in self.index[file_name]:
                msg.append(f"\t{file_path}\n")
        return "".join(msg)

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
            self.logger.info(f"Analyzing {file}")
            file: File

            # Test against other files with the same name
            same_name_files = self.name_index[file.name]
            self.logger.info("Comparing against same name:")
            if len(same_name_files) > 1:
                for i, file_a in enumerate(same_name_files):
                    for file_b in same_name_files[i + 1 :]:
                        self.__handle_compare(file_a, file_b)

            # Test against other files with the same size
            self.logger.info("Comparing against same size:")
            same_size_files = self.size_index[file.size]
            if len(same_size_files) > 1:
                for i, file_a in enumerate(same_size_files):
                    for file_b in same_size_files[i + 1 :]:
                        self.__handle_compare(file_a, file_b)

            # Test against other files with the same path
            self.logger.info("Comparing against same path:")
            same_path_files = self.path_index[file.dir_path]
            if len(same_path_files) > 1:
                for i, file_a in enumerate(same_path_files):
                    for file_b in same_path_files[i + 1 :]:
                        self.__handle_compare(file_a, file_b)

    def print_to_file(self, output_dir: Path):
        self.matches.print_to_file(output_dir)
        self.diffs.print_to_file(output_dir)
        self.content_name_dups.print_to_file(output_dir)
        self.content_path_dups.print_to_file(output_dir)
        self.name_dups.print_to_file(output_dir)
        self.content_dups.print_to_file(output_dir)

    def __handle_compare(self, file_a: File, file_b: File):
        # Return if two files have been compared already
        if self.comparison_cache[(file_a, file_b)]:
            return

        # Compare the two files and record
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

    # Pass a list of DirIndexes to combine with self
    def __combine_dir_index(self, others: List["DirIndex"]):
        # Transform single DirIndex input into a list
        if not isinstance(others, list):
            others = [others]
        dir_indexes: List["DirIndex"] = [self, *others]

        # Combine the indexes
        combined = defaultdict(list)
        for dir_index in dir_indexes:
            for file_name, file_paths in dir_index.index.items():
                if file_name not in combined:
                    combined[file_name] = []
                combined[file_name].extend(file_paths)

        # Build a combined name
        combined_name = "combined_"
        for dir_index in dir_indexes:
            combined_name += f"_{dir_index.name}"

        return DirIndex(name=combined_name, index=combined)
