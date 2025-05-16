import logging
from pathlib import Path
from collections import defaultdict

import utils
from comparison import Comparison, CompType
from file import File


class ComparisonIndex:
    def __init__(self, comparison_type: CompType):
        self.type = comparison_type
        self.index = defaultdict(list[File])

    def __repr__(self):
        return (
            f"ComparisonIndex(name={self.type.name!r}"
            f"entries={sum(len(v) for v in self.index.values())}, "
            f"keys={len(self.index)})"
        )

    def __str__(self):
        msg = [f"ComparisonIndex: {self.type.name}\n"]
        for key, file_list in self.index.items():
            msg.append(f"Key: {key}\n")
            for file in file_list:
                msg.append(f"\t{file.name} ({file.rel_path})\n")
                msg.append(f"\t\t{file.abs_path}\n")
        return "".join(msg)

    def write_to_file(self, output_dir: Path):
        utils.write_to_file(
            self.type, output_dir / self.type, str(self), is_timestamped=True
        )

    def add_comparison(self, comparison: Comparison):
        if comparison.type != self.type:
            raise ValueError(
                f"Attempted to add {comparison.type} to index of {self.type}"
            )
        logging.info(str(comparison))

        key_traits = tuple(
            trait for trait, is_key in comparison.comp_type.value.items() if is_key
        )

        for file in [comparison.fileA, comparison.fileB]:
            if file not in self.index[key_traits]:
                self.index[key_traits]
