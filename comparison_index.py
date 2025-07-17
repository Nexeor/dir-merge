import logging
from pathlib import Path
from collections import defaultdict
from typing import Dict

import utils
from comparison import Comparison, CompType
from file import File


class ComparisonIndex:
    def __init__(self, comparison_type: CompType):
        self.comp_type: CompType = comparison_type
        self.index: Dict[tuple:list] = defaultdict(list[File])

    def __repr__(self):
        return (
            f"ComparisonIndex(name={self.comp_type.name!r}"
            f"entries={sum(len(v) for v in self.index.values())}, "
            f"keys={len(self.index)})"
        )

    def __str__(self):
        msg = [
            f"ComparisonIndex: {self.comp_type.name}\n",
        ]
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
            self.comp_type.name,
            output_dir / self.comp_type.name,
            str(self),
            is_timestamped=True,
        )

    def add_file(self, file: File):
        key_traits = self._get_key_traits(file)
        self.index[key_traits].append(file)

    def add_comparison(self, comparison: Comparison):
        if comparison.comp_type != self.comp_type:
            raise ValueError(
                f"Attempted to add {comparison.comp_type} to index of {self.comp_type}"
            )
        logging.info(str(comparison))

        key_traits = self._get_key_traits(comparison.fileA)
        for file in [comparison.fileA, comparison.fileB]:
            if file not in self.index[key_traits]:
                self.index[key_traits].append(file)

    def set_comparisons(self, file_list: list[Comparison]):
        if not isinstance(file_list, list):
            file_list = [file_list]
        key_file = file_list[0]
        key_traits = self._get_key_traits(key_file)
        self.index[key_traits] = file_list

    def remove_comparisons(self, file: File):
        del self.index[self._get_key_traits(file)]

    def _get_key_traits(self, file: File) -> tuple:
        key_traits = []
        for trait, is_key in self.comp_type.value.items():
            if is_key:
                match trait:
                    case "path":
                        key_traits.append(file.rel_path.parent)
                    case "name":
                        key_traits.append(file.name)
                    case "content":
                        key_traits.append(file.quick_hash)
        return tuple(key_traits)
