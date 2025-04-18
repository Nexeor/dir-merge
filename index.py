import os
from collections import defaultdict
import logging


class DirIndex:
    def __init__(self, index_name):
        self.name = index_name
        self.logger = logging.getLogger(__name__)

        # index = { Filename : [Filepaths] }
        self.index = defaultdict(list)

    def __str__(self):
        msg = []
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
