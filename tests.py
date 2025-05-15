import unittest
from pathlib import Path

import config
from comparison import ComparisonResult
from utils import make_file_diff
from typing import Optional


# Generate test logs:
# Run this test suite with: python -m unittest tests.py
class TestUnion(unittest.TestCase):
    """
    Test that the most recent union files for each comparison type
    match their respective key files exactly.
    """

    def setUp(self):
        self.base_dir = Path(__file__).resolve().parent

    def test_build_union(self):
        for comparison_type in ComparisonResult:
            output_path: Path = (
                self.base_dir / config.OUTPUT_DIR_PATH / comparison_type.name
            )
            output_path = self._get_most_recent_file(output_path)
            key_path: Path = (
                self.base_dir / config.KEY_PATH / f"{comparison_type.name}_KEY.txt"
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
        if not make_file_diff(key_path, output_path):
            return True

        return False


if __name__ == "__main__":
    unittest.main()
