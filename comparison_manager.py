import logging
from collections import defaultdict
from typing import List, Dict, Tuple
from pathlib import Path

import cli
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
            name_comparisons = self._compare_file_against_group(file, same_name_files)
            found_name_compare = self._add_comparisons(name_comparisons)
            if not found_name_compare:
                logging.info("No same name comparisons found")

            # Test against other files with the same size
            same_size_files = dir_index.size_index[file.size]
            size_comparisons = self._compare_file_against_group(file, same_size_files)
            found_size_compare = self._add_comparisons(size_comparisons)
            if not found_size_compare:
                logging.info("No same size comparisons found")

            # If no comparison was found across either groups, mark as unique
            if not found_name_compare and not found_size_compare:
                logging.info("Unique file")
                self.comparisons[CompType.UNIQUE].add_file(file)

    def _compare_file_against_group(self, file: File, group: List[File]):
        comparisons = []
        for other_file in group:
            if file is not other_file and not (
                self.comparison_cache.get((self, other_file))
                or self.comparison_cache.get((self, other_file))
            ):
                new_comparison = file.compare_to(other_file)
                comparisons.append(new_comparison)

        return comparisons

    def _add_comparisons(self, comparisons: List[Comparison]):
        non_unique_added = False
        for comparison in comparisons:
            self.comparison_cache[(comparison.fileA, comparison.fileB)] = comparison
            if comparison.comp_type != CompType.UNIQUE:
                non_unique_added = True
                self.comparisons[comparison.comp_type].add_comparison(comparison)
        return non_unique_added

    def _compare_files(self, file_a: File, file_b: File):
        """Compares two files and caches the result"""
        logging.info(f"Comparing two files:\n\t{file_a}\n\t{file_b}")

        # Create comparison and cache it
        comparison = Comparison(file_a, file_b)
        self.comparisons[comparison.comp_type].add_comparison(comparison)
        print(type(self.comparisons[comparison.comp_type]))
        self.comparison_cache[(file_a, file_b)] = comparison
        return

    def resolve_all(self):
        for type in CompType:
            if type == CompType.MATCH:
                self.resolve_matches()
            elif type == CompType.UNIQUE:
                continue
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
