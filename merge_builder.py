import logging
from collections import defaultdict
from pathlib import Path
from typing import List, Dict

import cli
from file import File
from comparison_manager import ComparisonManager
from comparison import Comparison, CompType
from comparison_index import ComparisonIndex


class MergeBuilder:
    def __init__(self, build_path, comparison_manager: ComparisonManager):
        self.merge: Dict[Path : List[File]] = defaultdict(list)
        self.build_dir = build_path
        self.comparison_manager = comparison_manager
