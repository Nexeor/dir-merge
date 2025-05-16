import logging
from typing import List, Dict, Tuple

import cli
from file import File
from dir_index import DirIndex
from comparison_index import ComparisonIndex
from comparison import Comparison, CompType


class ComparisonManager:
    def __init__(self, name):
        # Create a ComparisonIndex for each CompType
        self.comparisons: Dict[CompType:Comparison] = {}
        for type in CompType:
            self.comparisons[type.name] = ComparisonIndex(type)

        self.comparison_cache: Dict[Tuple[File, File] : Comparison]
        self.unique: List[File] = []  # List of "unique" files

    def write_str_to_file(self, name):
        for comp_type in CompType:
            ComparisonIndex.write_to_file()

    # Given a valid DirIndex, compare the files within that DirIndex and
    # add the comparisons to the manager
    def compare_files(self, dir_index: DirIndex):
        for file in dir_index.file_list:
            logging.info(f"\nAnalyzing {file}")

            # Test against other files with the same name
            logging.info("Comparing against same name:")
            same_name_files = dir_index.name_index[file.name]
            found_name_compare = self._compare_group(same_name_files)
            if not found_name_compare:
                logging.info("No same name matches found")

            # Test against other files with the same size
            logging.info("Comparing against same size:")
            same_size_files = dir_index.name_index[file.size]
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
                        self.comparison_cache[(file_a, file_b)]
                        or self.comparison_cache[(file_b, file_a)]
                    ):
                        self._compare_files(file_a, file_b)
                        found = True
        return found

    def _compare_files(self, file_a: File, file_b: File):
        """Compares two files and caches the result"""

        # Return early if comparison already cached
        if (
            self.comparison_cache[(file_a, file_b)]
            or self.comparison_cache[(file_b, file_a)]
        ):
            return True

        # Create comparison and cache it
        comparison: Comparison = file_a.compare_to(file_b)
        self.comparisons[comparison.comp_type].add_comparison(comparison)
        self.comparison_cache[(file_a, file_b)] = comparison

    def resolve_matches(self):
        match_index: ComparisonIndex = self.comparisons[CompType.MATCH]
        for key, matches in match_index.index.items():
            logging.info(
                f"Resolving MATCH: {repr(matches)}\n\tChoosing: {repr(matches)}"
            )

            # Only keep one of the matches for each comparison
            match_index[key] = matches[0]

    def resolve_path_name_dup(self):
        path_name_index: ComparisonIndex = self.comparisons[CompType.PATH_NAME_DUP]
        for key, dup_list in path_name_index.index.items():
            logging.info(f"Resolving PATH-NAME Dup: {repr(dup_list)}")

            # Display files
            cli.display_files(
                msg="PATH-NAME DUP: Files have the same name and path but have different content",
                file_list=dup_list,
            )
            cli.prompt_build_diff(dup_list)
            user_choice = cli.prompt_keep_options(dup_list, link_paths=True)

            # TODO: Resolve user choice

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
        diff_log = utils.make_file_diff(to_compare[0].abs_path, to_compare[1].abs_path)
        if not diff_log:
            print("No differences found?")
        return diff_log

    def resolve_content_name_dup(self):
        for _, dups in self.content_name_dups.index.items():
            logging.info(f"Resolving content-name dup: {repr(dups)}")

            cli.display_files(
                msg="CONTENT-NAME-DUP: Files have same content and name, but different path",
                file_list=dups,
            )
            self._prompt_keep_options(dups)

    def resolve_content_path_dup(self):
        for _, dups in self.content_path_dups.index.items():
            logging.info(f"Resolving content-path dup: {repr(dups)}")
            cli.display_files(
                msg="CONTENT-PATH-DUP: Files have the same content and path, but different name",
                file_list=dups,
            )
            self._prompt_keep_options(dups)

    def resolve_content_dup(self):
        for _, dups in self.content_dups.index.items():
            logging.info(f"Resolving content dup: {repr(dups)}")

            cli.display_files(
                msg="CONTENT-DUP: Files have same content, but have different name and path",
                file_list=dups,
            )

            self._prompt_keep_options(dups)

    def resolve_name_dup(self):
        for _, dups in self.name_dups.index.items():
            print(type(dups))
            logging.info(f"Resolving name dup: {repr(dups)}")

            cli.display_files(
                msg="NAME-DUP: Files have same name, but different content and path",
                file_list=dups,
            )

            self._prompt_keep_options(dups, link_paths=True)
