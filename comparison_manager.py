import logging
from collections import defaultdict
from typing import List, Dict, Tuple
from pathlib import Path

import cli
import utils
from file import File
from dir_index import DirIndex
from comparison_index import ComparisonIndex
from comparison import Comparison, CompType


class ComparisonManager:
    def __init__(self):
        # Create a ComparisonIndex for each CompType
        self.comparisons: Dict[CompType:Comparison] = {}
        for type in CompType:
            self.comparisons[type] = ComparisonIndex(type)

        self.comparison_cache: Dict[Tuple[File, File] : Comparison] = defaultdict()
        self.unique: List[File] = []  # List of "unique" files

    def __repr__(self):
        return (
            f"ComparisonManager(comparison_types={list(self.comparisons.keys())}, "
            f"cached_comparisons={len(getattr(self, 'comparison_cache', {}))}, "
            f"unique_files={len(self.unique)})"
        )

    def __str__(self):
        return (
            f"ComparisonManager managing {len(self.unique)} unique files "
            f"and {len(getattr(self, 'comparison_cache', {}))} cached comparisons "
            f"across {len(self.comparisons)} comparison types"
        )

    def write_to_file(self, output_path: Path):
        for type, index in self.comparisons.items():
            index: ComparisonIndex
            index.write_to_file(output_path)

    # Given a valid DirIndex, compare the files within that DirIndex and
    # add the comparisons to the manager
    def add_dir_index(self, dir_index: DirIndex):
        for file in dir_index.file_list:
            logging.info(f"\nAnalyzing {file}")

            # Test against other files with the same name
            logging.info("Comparing against same name:")
            same_name_files = dir_index.name_index[file.name]
            # print(same_name_files)
            found_name_compare = self._compare_group(same_name_files)
            # print(found_name_compare)
            if not found_name_compare:
                logging.info("No same name matches found")

            # Test against other files with the same size
            logging.info("Comparing against same size:")
            same_size_files = dir_index.size_index[file.size]
            print(same_size_files)
            found_size_compare = self._compare_group(same_size_files)
            if not found_size_compare:
                logging.info("No same size matches found")

            if not found_name_compare and not found_size_compare:
                logging.info("Unique file")
                self.unique.append(file)

    def _compare_group(self, file_list):
        """Compares all unique pairs in a group. Returns True if any comparison was found within the group."""
        found = False
        if len(file_list) > 1:
            for i, file_a in enumerate(file_list):
                for file_b in file_list[i + 1 :]:
                    if not (
                        self.comparison_cache.get((file_a, file_b))
                        or self.comparison_cache.get((file_b, file_a))
                    ):
                        self._compare_files(file_a, file_b)
                        found = True
                    else:
                        logging.info(f"Comparison already cached")

        return found

    def _compare_files(self, file_a: File, file_b: File):
        """Compares two files and caches the result"""
        logging.info(f"Comparing two files:\n\t{file_a}\n\t{file_b}")

        # Create comparison and cache it
        comparison = Comparison(file_a, file_b)
        self.comparisons[comparison.comp_type].add_comparison(comparison)
        print(type(self.comparisons[comparison.comp_type]))
        self.comparison_cache[(file_a, file_b)] = comparison

    def resolve_all(self):
        for type in CompType:
            if type == CompType.MATCH:
                self.resolve_matches()
            else:
                self.resolve_dups(type)

    def resolve_matches(self):
        match_index: ComparisonIndex = self.comparisons[CompType.MATCH]
        for key, matches in match_index.index.items():
            logging.info(
                f"Resolving MATCH: {repr(matches)}\n\tChoosing: {repr(matches)}"
            )

            # Only keep one of the matches for each comparison
            match_index.set_comparisons(matches[0])

    def resolve_dups(self, type: CompType):
        comparison_index: ComparisonIndex = self.comparisons[type]
        for key, dup_list in comparison_index.index.items():
            logging.info(f"Resolving {type.name} dup: {repr(dup_list)}")

            cli.display_files(msg=f"Resolving {type.name} dup", file_list=dup_list)
            if not type.value["content"]:
                cli.prompt_build_diff(dup_list)
            user_choice = cli.prompt_keep_options(dup_list, link_paths=True)
            comparison_index.set_comparisons(user_choice)
