import unittest
from unittest.mock import patch
from pathlib import Path

import config
import utils
from log_config import setup_logging
from dir_merge_runner import index_from_paths
from comparison import CompType
from typing import Optional


# Run test suite: python -m unittest tests.py
class TestUnion(unittest.TestCase):
    """
    Test that the most recent union files for each comparison type
    match their respective key files exactly.
    """

    def setUp(self):
        setup_logging()
        self.base_dir = Path(__file__).resolve().parent

        self.patcher = patch(
            "cli.prompt",
            side_effects=["2", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1"],
        )
        self.mock_prompt = self.patcher.start()  # 👈 PATCH APPLIES HERE
        self.addCleanup(self.patcher.stop)

        index_from_paths(
            [(self.base_dir / config.TEST_PATH_A), (self.base_dir / config.TEST_PATH_B)]
        )

    def test_build_union(self):
        for comparison_type in CompType:
            self.key_check(comparison_type.name)
        self.key_check("MERGE")

    def key_check(self, test_file_name):
        output_path: Path = self.base_dir / config.OUTPUT_DIR_PATH / test_file_name
        output_path = self._get_most_recent_file(output_path)
        key_path: Path = self.base_dir / config.KEY_PATH / f"{test_file_name}_KEY.txt"
        print(
            f"Testing {test_file_name}\n"
            f"\tOutput: {utils.make_link(output_path)}\n"
            f"\tKey: {utils.make_link(key_path)}"
        )
        self.assertTrue(self.is_equal(key_path, output_path))

    def _get_most_recent_file(self, folder_path: Path) -> Optional[Path]:
        folder = Path(folder_path)
        files = [f for f in folder.iterdir() if f.is_file()]
        if not files:
            return None
        most_recent_file = max(files, key=lambda f: f.stat().st_birthtime)
        return most_recent_file

    def is_equal(
        self,
        key_path: Path,
        output_path: Path,
    ):
        # If no file diff returned, then files are equal
        if not utils.make_file_diff(key_path, output_path):
            return True

        return False


if __name__ == "__main__":
    unittest.main()
