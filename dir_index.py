import os
import logging

from pathlib import Path
from collections import defaultdict
from typing import List

from utils import get_relative_to_base_path, check_file_diff

# Path to cloned repo
PATH_A = r"C:\Users\trjji\Documents\Coding Projects\obsidian-helpers\temp_clone"
# Path to local vault
PATH_B = r"C:\Users\trjji\Documents\Obsidian Vault"


class DirIndex:
    def __init__(self, name, index=None):
        self.name = name
        self.logger = logging.getLogger(__name__)

        # index = { Filename : [Filepaths] }
        if index:
            self.index = index
        else:
            self.index = defaultdict(list)

    def __str__(self):
        msg = [f"Index: {self.name}\n"]
        for file_name in self.index:
            msg.append(f"{file_name}\n")
            for file_path in self.index[file_name]:
                msg.append(f"\t{file_path}\n")
        return "".join(msg)

    # Add all files in the given directory to the index and return the dict
    def index_dir(self, dir_path):
        for dirpath, dirnames, filenames in os.walk(dir_path):
            # Modify dirnames in place so os.walk doesn't traverse hidden dirs
            dirnames[:] = [dir for dir in dirnames if dir[0] != "."]

            # Get absolute path
            abs_dir_path = os.path.normpath(os.path.abspath(dirpath))
            self.logger.info(f"Indexing directory: {abs_dir_path}")

            # Iterate over files for indexing
            for filename in filenames:
                file_path = os.path.join(abs_dir_path, filename)
                self.logger.info(f"\tIndexing File: {file_path}")

                # Add file to index
                self.index[filename].append(file_path)

        return self.index

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

        diff = self.find_diff(other)

        return {"DUP": combined_dup, "DNE": combined_dne, "DIFF": diff}

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
                    relative_path = get_relative_to_base_path(path)
                    same_rel_paths[relative_path].append(path)
                except ValueError as e:
                    print(e)
                    logging.error(e)
                    same_rel_paths["<unmatched>"].append(path)

        # Check matching relative paths for file equality
        for rel_path, abs_paths in same_rel_paths.items():
            for i, abs_path_A in enumerate(abs_paths):
                for abs_path_B in abs_paths[i + 1 :]:
                    diff_log = check_file_diff(abs_path_A, abs_path_B)

                    if diff_log:
                        diff_logs[rel_path].append(diff_log)

        return DirIndex(name=f"diff_{self.name}_{other.name}", index=diff_logs)

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
