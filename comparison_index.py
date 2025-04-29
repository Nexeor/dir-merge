from datetime import datetime
from pathlib import Path

from collections import defaultdict
from comparison import Comparison


class ComparisonIndex:
    def __init__(self, name, comparison_type):
        self.name = name
        self.type: Comparison = comparison_type # The comparison type this index holds
        self.index = defaultdict(list)
    
    def __repr__(self):
        msg = [f"{self.name}\n"]
        for key, file_list in self.index.items():
            msg.append(f"{key}:\n")
            for file in file_list:
                msg.append(f"\t{file}\n")
        return "".join(msg)
    
    def print_to_file(self, output_dir: Path):
        # Create output dir and file
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_path = output_dir / self.name / f"{self.name}-{timestamp}.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write output
        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(repr(self))


    def add_comparison(self, comparison: Comparison):
        if comparison.type != self.type:
            raise ValueError(f"Attempted to add {comparison.type} to index of {self.type}")
        
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


