import difflib
import filecmp
import os
import logging

from pathlib import Path
from collections import defaultdict
from typing import Dict, List

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

    # Given two index objects, do a full comparison
    def compare_to(self, other):
        return True

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

        # Combine the two indexes into one
        combined = defaultdict(list)
        for elem in (self, other):
            for file_name, file_paths in elem.index.items():
                if file_name not in combined:
                    combined[file_name] = []
                combined[file_name].extend(file_paths)

        # Regroup index by matching relative path, { relpath : [abs_paths] }
        same_rel_paths = defaultdict(list)
        for file_name, file_paths in combined.items():
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


# Match given path to a base path and extract the relative path
def get_relative_to_base_path(full_path):
    path = Path(full_path)

    for base in [PATH_A, PATH_B]:
        if path.is_relative_to(base):
            return path.relative_to(base)

    raise ValueError(
        f"The path {full_path} is not relative to any of the defined base paths."
    )


def check_file_diff(file_path_A, file_path_B):
    diff_log = None
    if not filecmp.cmp(file_path_A, file_path_B, shallow=False):
        with open(file_path_A) as base:
            base_content = base.readlines()
        with open(file_path_B) as comp:
            comp_content = comp.readlines()

        diff_log = list(
            difflib.unified_diff(base_content, comp_content, file_path_A, file_path_B)
        )
    return diff_log
