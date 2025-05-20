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

    @classmethod
    def setUpClass(cls):
        setup_logging()
        cls.base_dir = Path(__file__).resolve().parent

        cls.patcher = patch(
            "cli.prompt",
            side_effects=["2", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1"],
        )
        cls.mock_prompt = cls.patcher.start()  # 👈 PATCH APPLIES HERE

        index_from_paths(
            [(cls.base_dir / config.TEST_PATH_A), (cls.base_dir / config.TEST_PATH_B)]
        )

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    def test_build_union(self):
        for comparison_type in CompType:
            self.key_check(comparison_type.name)
        self.key_check("MERGE")

    def test_expected_files(self):
        output_path = self._get_most_recent_dir(
            Path(config.OUTPUT_DIR_PATH / "COMPLETE_MERGES")
        )

        expected_files = {
            "same_path/match-test.txt",
            "same_path/path-name-dup-test.txt",
            "same_path/content-path-test-one.txt",
            "diff_path_one/content-name-dup-test.txt",
            "diff_path_one/name-dup-test.txt",
            "diff_path_one/content-dup-test-one.txt",
            "diff_path_one/unique-test-one.txt",
            "diff_path_two/unique-test-two.txt",
        }

        found_files = {
            str(path.relative_to(output_path)).replace("\\", "/")
            for path in output_path.rglob("*")
            if path.is_file()
        }

        print("\nChecking all files written to disk...")
        assert found_files == expected_files, (
            f"File mismatch:\nMissing: {expected_files - found_files}\n"
            f"Unexpected: {found_files - expected_files}"
        )

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

    def _get_most_recent_dir(self, folder_path: Path) -> Optional[Path]:
        folder = Path(folder_path)
        dirs = [d for d in folder.iterdir() if d.is_dir()]
        if not dirs:
            return None
        try:
            most_recent_dir = max(dirs, key=lambda d: d.stat().st_birthtime)
        except AttributeError:
            # Fallback for platforms without st_birthtime
            most_recent_dir = max(dirs, key=lambda d: d.stat().st_ctime)
        return most_recent_dir

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
