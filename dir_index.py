import logging

from pathlib import Path
from collections import defaultdict
from typing import List, Dict

import utils
from file import File


class DirIndex:
    def __init__(self, name_index=None, size_index=None):
        self.logger = logging.getLogger(__name__)
        self.base_dir_paths = []

        # List all files in index
        self.file_list: List[File] = []

        # Trait indexes
        self.name_index: Dict[str : List[File]] = name_index or defaultdict(list)
        self.size_index: Dict[int : List[File]] = size_index or defaultdict(list)

    def __repr__(self):
        return (
            f"file_count={len(self.file_list)}, "
            f"name_index_keys={len(self.name_index)}, "
            f"size_index_keys={len(self.size_index)})"
        )

    def __str__(self):
        return (
            f"{len(self.file_list)} files indexed, "
            f"{len(self.name_index)} name keys, "
            f"{len(self.size_index)} size keys"
        )

    def print_trait_indexes_to_file(self, output_dir: Path):
        # Gather indexes
        indexes = {
            "NAME_INDEX": self.name_index,
            "SIZE_INDEX": self.size_index,
        }
        for name, index in indexes.items():
            self._print_index_to_file(name, index, output_dir)

    def _print_index_to_file(self, index_name: str, index: Dict, output_dir: Path):
        # Generate the string of this index
        msg = []
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
                    self.file_list.append(file)
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
