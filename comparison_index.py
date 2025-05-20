import logging
from pathlib import Path
from collections import defaultdict
from typing import Dict

import utils
from comparison import Comparison, CompType
from file import File


class ComparisonIndex:
    def __init__(self, comparison_type: CompType):
        self.type: CompType = comparison_type
        self.index: Dict[tuple:list] = defaultdict(list[File])

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
                file: File

                msg.append(f"\t{file.name} ({file.rel_path})\n")
                msg.append(f"\t\t{file.abs_path}\n")
        return "".join(msg)

    def write_to_file(self, output_dir: Path):
        # print(output_dir)
        # print(self.type.name)
        utils.write_to_file(
            self.type.name, output_dir / self.type.name, str(self), is_timestamped=True
        )

    def add_comparison(self, comparison: Comparison):
        if comparison.comp_type != self.type:
            raise ValueError(
                f"Attempted to add {comparison.type} to index of {self.type}"
            )
        logging.info(str(comparison))

        key_traits = self._get_key_traits(comparison)
        for file in [comparison.fileA, comparison.fileB]:
            if file not in self.index[key_traits]:
                self.index[key_traits].append(file)

    def set_comparisons(self, comparisons: list[Comparison]):
        if type(comparisons) != list:
            comparisons = [comparisons]
        key_comparison = comparisons[0]
        key_traits = self._get_key_traits(key_comparison)
        self.index[key_traits] = comparisons

    def _get_key_traits(self, comparison: Comparison) -> tuple:
        key_traits = []
        for trait, is_key in comparison.comp_type.value.items():
            if is_key:
                match trait:
                    case "path":
                        key_traits.append(comparison.fileA.rel_path.parent)
                    case "name":
                        key_traits.append(comparison.fileA.name)
                    case "content":
                        key_traits.append(comparison.fileA.quick_hash)
        return tuple(key_traits)
