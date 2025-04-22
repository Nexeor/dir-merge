# Duplicates: Choose which duplicates to keep and which to get rid of
# Match/DNE: Copy over
# Diff: Choose which version to keep

# 1) Combine MATCH with DNE and use them to generate base dir
# 2) For each DUP, choose which paths to keep
# 3) For each DIFF, choose which version to keep

import sys
import logging

from pathlib import Path

TARGET_PATH = r"C:\Users\trjji\Documents\Coding Projects\obsidian-helpers\combined"


# Given the root_path,
def setup_root(root_path):
    root = Path(root_path)

    if root.exists():
        msg = f"Aborting build: root directory {root} already exists"
        print(msg)
        logging.error(msg)
        sys.exit(1)

    try:
        root.mkdir(parents=True)
        logging.info()

    except Exception as e:
        msg = f"Failed to create root directory due to {e}"
        print(msg)
        logging.exception(msg)
        sys.exit(1)
