import logging
from pathlib import Path
from collections import defaultdict

import utils
from comparison import Comparison, ComparisonResult
from file import File


class ComparisonIndex:
    def __init__(self, name, comparison_type):
        self.name = name
        self.type: ComparisonResult = (
            comparison_type  # The comparison type this index holds
        )
        self.index = defaultdict(list[File])

    def __repr__(self):
        return (
            f"ComparisonIndex(name={self.name!r}, type={self.type}, "
            f"entries={sum(len(v) for v in self.index.values())}, "
            f"keys={len(self.index)})"
        )

    def __str__(self):
        msg = [f"ComparisonIndex: {self.name} (Type: {self.type})\n"]
        for key, file_list in self.index.items():
            msg.append(f"Key: {key}\n")
            for file in file_list:
                msg.append(f"\t{file.name} ({file.rel_path})\n")
        return "".join(msg)

    def print_to_file(self, output_dir: Path):
        utils.write_to_file(
            self.name, output_dir / self.name, str(self), is_timestamped=True
        )

    def add_comparison(self, comparison: Comparison):
        if comparison.type != self.type:
            raise ValueError(
                f"Attempted to add {comparison.type} to index of {self.type}"
            )
        logging.info(str(comparison))

        key_parts = {
            "name": comparison.fileA.name,
            "path": comparison.fileA.rel_path,
            "content": comparison.fileA.quick_hash,
        }
        key = tuple(key_parts[part] for part in self.type.value)

        index_entry = self.index[key]
        for file in [comparison.fileA, comparison.fileB]:
            if file not in index_entry:
                index_entry.append(file)
