import logging
from collections import defaultdict
from pathlib import Path
from typing import List, Dict

import cli
from file import File
from comparison_manager import ComparisonManager
from comparison import Comparison, CompType
from comparison_index import ComparisonIndex


class MergeBuilder:
    def __init__(self, build_path, comparison_manager: ComparisonManager):
        self.merge: Dict[Path : List[File]] = defaultdict(list)
        self.build_dir = build_path
        self.comparison_manager = comparison_manager

    def resolve_all(self):
        for type in CompType:
            if type == CompType.MATCH:
                self.resolve_matches()
            else:
                self.resolve_dups(type)

    def resolve_matches(self):
        match_index: ComparisonIndex = self.comparison_manager.comparisons[
            CompType.MATCH
        ]
        for key, matches in match_index.index.items():
            logging.info(
                f"Resolving MATCH: {repr(matches)}\n\tChoosing: {repr(matches)}"
            )

            # Keep one match for merge
            print(type(matches[0]))
            self.merge[matches[0].fileA.dir_path] = matches[0]

    def resolve_dups(self, type: CompType):
        comparison_index: ComparisonIndex = self.comparison_manager.comparisons[type]
        for key, dup_list in comparison_index.index.items():
            logging.info(f"Resolving {type.name} dup: {repr(dup_list)}")

            cli.display_files(msg=f"Resolving {type.name} dup", file_list=dup_list)
            if not type["content"]:
                cli.prompt_build_diff(dup_list)
            user_choice = cli.prompt_keep_options(dup_list, link_paths=True)

            if type(user_choice) == list:
                user_choice: List[File]
                key_path = user_choice[0].dir_path
            else:
                user_choice: File
                key_path = user_choice.dir_path
            self.merge[key_path].extend(user_choice)
