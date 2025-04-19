import difflib
import filecmp
import os
import logging

from collections import defaultdict
from typing import Dict, List


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
        # Combine the two indexes
        combined = defaultdict(list)
        for elem in (self, other):
            for file_name, file_paths in elem.index.items():
                if file_name not in combined:
                    combined[file_name] = []
                combined[file_name].extend(file_paths)

        # Check for differences
        for file_name, file_paths in combined.items():
            for path in file_paths:
                # NEED TO GET RELATIVE PATH HERE
                if path in other.index[file_name]:
                    check_file_diff(path)

        return DirIndex(name=f"diff_{self.name}_{other.name}", index=combined)


def check_file_diff(file_path_A, file_path_B):
    if not filecmp.cmp(file_path_A, file_path_B, shallow=False):
        with open(file_path_A) as base:
            base_content = base.readlines()
        with open(file_path_B) as comp:
            comp_content = comp.readlines()

        diff_log = list(
            difflib.unified_diff(base_content, comp_content, file_path_A, file_path_B)
        )
    return diff_log
