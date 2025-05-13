from pathlib import Path

DEFAULT_PATH_A = Path("test_dirs/temp_clone_local")
DEFAULT_PATH_B = Path("test_dirs/temp_clone_remote")

TEST_PATH_A = Path(
    "C:/Users/trjji/Documents/Coding Projects/obsidian-helpers/test_dirs/test_dir_one"
)
TEST_PATH_B = Path(
    "C:/Users/trjji/Documents/Coding Projects/obsidian-helpers/test_dirs/test_dir_two"
)

OUTPUT_DIR_PATH = Path("./.results")

MISSING_PATH = Path(OUTPUT_DIR_PATH / "missing")
DIFF_PATH = Path(OUTPUT_DIR_PATH / "diff")
DUP_PATH = Path(OUTPUT_DIR_PATH / "duplicate")
MATCH_PATH = Path(OUTPUT_DIR_PATH / "matches")
LOG_PATH = Path(OUTPUT_DIR_PATH / "logs")
