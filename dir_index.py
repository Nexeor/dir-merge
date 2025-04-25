import os
import logging

from pathlib import Path
from collections import defaultdict
from typing import List, Dict

import utils
from file import File


class DirIndex:
    def __init__(self, name, name_index=None, path_index=None, size_index=None):
        self.name = name
        self.logger = logging.getLogger(__name__)
        self.name_index: Dict[str : List[File]] = name_index or defaultdict(list)
        self.path_index: Dict[str : List[File]] = path_index or defaultdict(list)
        self.size_index: Dict[int : List[File]] = size_index or defaultdict(list)

    def __str__(self):
        msg = [f"Index: {self.name}\n"]
        for file_name in self.index:
            msg.append(f"{file_name}\n")
            for file_path in self.index[file_name]:
                msg.append(f"\t{file_path}\n")
        return "".join(msg)

    # Add all files in the given dire ctory to the index and return the dict
    def index_dir(self, base_dir_path):
        # Recursively iterate over filetree and add to index
        base_dir_path = Path(base_dir_path)
        for abs_path in base_dir_path.rglob("*"):
            if not utils.is_hidden(abs_path):
                if abs_path.is_file():
                    self.logger.info(
                        f"Indexing file: \n\tName: {abs_path.name}\n\tPath: {abs_path}"
                    )
                    file = File(abs_path)
                    self.name_index[file.name].append(file)
                    self.path_index[file.path].append(file)
                    self.size_index[file.size].append(file)
                elif abs_path.is_dir():
                    self.logger.info(f"Indexing directory: {abs_path}")

    # Scan all of the files in the index for matches
    def find_matches(self):
        for filename, files in self.name_index.items():
            for file in files:
                print(file)

    def find_compare(self):
        for filename, files in self.name_index.items():
            print(f"{filename} : {files}")
            # Other files with same name exist
            if len(files) > 1:
                for i, file in enumerate(files):
                    for file in files[i + 1 :]:
                        print(f"\t{file}")
            # Name is unique
            else:
                print(f"\t{file}")

    # Compare this index object to the other. Return a dict containing the
    # duplicates, dne's, and diff files
    def compare_to(self, other: "DirIndex"):
        self_dup = self.find_self_duplicates()
        other_dup = other.find_self_duplicates()
        cross_dup = self.find_cross_duplicates(other_dup)
        combined_dup = self_dup.__combine_dir_index([other_dup, cross_dup])

        self_dne = self.find_DNE(other)
        other_dne = other.find_DNE(self)
        combined_dne = self_dne.__combine_dir_index(other_dne)

        diff, match = self.find_diff(other)
        return {"DUP": combined_dup, "DNE": combined_dne, "DIFF": diff, "MATCH": match}

    # Return an index of all duplicates within this index
    # Duplicate: A file with the same name as another, but a different path
    def find_self_duplicates(self):
        duplicates = {
            file_name: paths
            for file_name, paths in self.index.items()
            if len(paths) > 1
        }

        return DirIndex(name=f"internal_dup_{self.name}", index=duplicates)

    # Return an index of all duplicates shared between self and other
    def find_cross_duplicates(self, other: "DirIndex"):
        duplicates = DirIndex(name=f"cross_dup_{self.name}_{other.name}")
        for file_name in self.index:
            if file_name in other.index:
                duplicates.index[file_name].extend(self.index[file_name])
                duplicates.index[file_name].extend(other.index[file_name])

        return duplicates

    # Return an index containing the files that only exist in self
    # DNE: A file with a unique name that is present in only one index
    def find_DNE(self, other: "DirIndex"):
        dne = DirIndex(name=f"dne_{self.name}_{other.name}")
        for file_name in self.index:
            if file_name not in other.index:
                dne.index[file_name].extend(self.index[file_name])

        return dne

    # Return an index containing the files that are "diff" across the self and other
    # Diff: A file that appears in both indexes with the same name and relative path, but
    # contain different content
    def find_diff(self, other: "DirIndex"):
        diff_logs = defaultdict(list)

        combined = self.__combine_dir_index(other)

        # Regroup index by matching relative path, { relpath : [abs_paths] }
        same_rel_paths = defaultdict(list)
        for file_name, file_paths in combined.index.items():
            for path in file_paths:
                try:
                    relative_path = utils.get_relative_to_base_path(path)
                    same_rel_paths[relative_path].append(path)
                except ValueError as e:
                    print(e)
                    logging.error(e)
                    same_rel_paths["<unmatched>"].append(path)

        # Check matching relative paths for file equality
        matches = defaultdict(list)
        for rel_path, abs_paths in same_rel_paths.items():
            for i, abs_path_A in enumerate(abs_paths):
                for abs_path_B in abs_paths[i + 1 :]:
                    diff_log = utils.check_file_diff(abs_path_A, abs_path_B)
                    file_name = Path(abs_path_A).name

                    if diff_log:
                        diff_logs[rel_path].append(diff_log)
                    else:
                        matches[file_name].extend((abs_path_A, abs_path_B))

        return (diff_logs, matches)

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
