from pathlib import Path

# Path to cloned repo
PATH_A = Path("C:/Users/trjji/Code/obsidian-helpers/temp_clone")
# Path to local vault
PATH_B = Path("C:/Users/trjji/OneDrive/Documents/The Hivemind")
# Path to ouput dir
OUTPUT_DIR_PATH = Path("./.results")

MISSING_PATH = Path(OUTPUT_DIR_PATH / "missing")
DIFF_PATH = Path(OUTPUT_DIR_PATH / "diff")
DUP_PATH = Path(OUTPUT_DIR_PATH / "duplicate")
MATCH_PATH = Path(OUTPUT_DIR_PATH / "matches")
LOG_PATH = Path(OUTPUT_DIR_PATH / "logs")
