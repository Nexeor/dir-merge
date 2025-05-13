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
        self.all_files: List[File] = []
        self.name_index: Dict[str : List[File]] = name_index or defaultdict(list)
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

        # Union index { rel_path : File }
        self.union: Dict[Path : List[File]] = defaultdict(list)

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

    def print_comparison_to_file(self, output_dir: Path):
        """Write comparison indexes and unique files to files in output_dir."""
        # Gather comparison indexes and write to file
        comparison_indexes = [
            self.matches,
            self.diffs,
            self.content_name_dups,
            self.content_path_dups,
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
                    self.all_files.append(file)
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
            return True

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

    def resolve_matches(self):
        for _, matches in self.matches.index.items():
            self.logger.info(
                f"Resolving MATCH: {repr(matches)}\n\tChoosing: {repr(matches)}"
            )

            to_keep: File = matches[0]
            self.union[to_keep.rel_path].append(to_keep)

    def resolve_diff(self):
        for _, diffs in self.diffs.index.items():
            self.logger.info(f"Resolving DIFF: {repr(diffs)}")

            # Display files
            cli.display_files(
                "DIFF: Files have the same name and path but have different content",
                diffs,
            )

            # Ask for line-by-line DIFF until user continues
            msg = "Would you like to view a line-by-line comparison?"
            yes_no_choices = ["Yes", "No"]
            comparing = True
            while comparing:
                user_choice = cli.prompt_user_options(msg, yes_no_choices)
                match user_choice:
                    # Generate a line-by-line
                    case 1:
                        diff_log = self._generate_line_by_line_diff(diffs)
                        for line in diff_log:
                            print(line)
                        if len(diffs) == 2:
                            comparing = False
                    # Continue
                    case 2:
                        comparing = False

            self._prompt_keep_options(diffs, link_paths=True)

    # Given a list of diff files, prompt the user to pick two to generate a diff from
    def _generate_line_by_line_diff(self, diffs: List[File]):
        to_compare: List[File] = []
        if len(diffs) == 2:
            to_compare = [diffs[0], diffs[1]]
        else:
            for i in range(2):
                msg = f"Choose {'first' if i == 0 else 'second'} file to compare"
                diff_files = [
                    diff_file
                    for diff_file in diffs
                    if diff_file.abs_path not in to_compare
                ]

                user_choice = cli.prompt_user_options(
                    msg,
                    [diff_file.abs_path for diff_file in diff_files],
                )
                to_compare.append(diff_files[user_choice])
        diff_log = utils.check_file_diff(to_compare[0].abs_path, to_compare[1].abs_path)
        if not diff_log:
            print("No differences found?")
        return diff_log

    def resolve_content_name_dup(self):
        for _, dups in self.content_name_dups.index.items():
            self.logger.info(f"Resolving content-name dup: {repr(dups)}")

            cli.display_files(
                "CONTENT-NAME-DUP: Files have same content and name, but different path",
                dups,
            )
            self._prompt_keep_options(dups)

    def resolve_content_dup(self):
        for _, dups in self.content_dups.index.items():
            self.logger.info(f"Resolving content dup: {repr(dups)}")

            cli.display_files(
                msg="CONTENT-DUP: Files have same content, but have different name and path",
                file_list=dups,
            )

            self._prompt_keep_options(dups)

    def resolve_name_dup(self):
        for _, dups in self.name_dups.index.items():
            print(type(dups))
            self.logger.info(f"Resolving name dup: {repr(dups)}")

            cli.display_files(
                msg="NAME-DUP: Files have same name, but different content and path",
                file_list=dups,
            )

            self._prompt_keep_options(dups, link_paths=True)

    def _prompt_keep_options(self, file_list: List[File], link_paths=False):
        msg = "Choose how to resolve:"
        options = ["Keep one", "Keep all (system will auto-rename)", "Delete all"]
        user_choice = cli.prompt_user_options(msg, options)
        match user_choice:
            case 1:
                msg = "Choose which file to keep"
                choices = [
                    (utils.make_link(file.abs_path) if link_paths else file.abs_path)
                    for file in file_list
                ]
                user_choice = cli.prompt_user_options(msg, choices)
                print(user_choice)
                to_keep = file_list[user_choice]
                self.union[to_keep.rel_path].append(to_keep)
            case 2:
                for i, file in enumerate(file_list):
                    file.name = f"{file.name}_v{i}"
                    self.union[file.rel_path].append(file)
            case 3:
                pass
