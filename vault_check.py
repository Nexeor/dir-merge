from collections import defaultdict
import filecmp
import os
import subprocess
import difflib
import logging
from datetime import datetime
from urllib.parse import quote

from log_config import setup_logging
from index import DirIndex

# The remote branch to be compared against
BRANCH_NAME = "main"
# URL to clone remote repo
REMOTE_URL = "https://github.com/Nexeor/Notes.git"
# List of dirs to ignore
IGNORE_DIRS = [".git", ".obsidian"]
# Path to ouput dir
OUTPUT_DIR_PATH = "./results"
# Path to cloned repo
PATH_A = r"C:\Users\trjji\Documents\Coding Projects\obsidian-helpers\temp_clone"
# Path to local vault
PATH_B = r"C:\Users\trjji\Documents\Obsidian Vault"


def get_remote():
    subprocess.run(
        ["git", "clone", "-b", BRANCH_NAME, "--single-branch", REMOTE_URL, PATH_A]
    )


# Compare the modified directory to the remote copy
# No Change:
# 1) Exists in base_dir and comp_dir
# 2) Exists in same place,
# 3) Contains same content
# OR
# 1) Only exists in base_dir
# Upload from mod:
# 1) Exists in comp_dir but not in base_dir
# Choose between:
# 1) Exists in comp_dir and base_dir
# 2) Exists in same place
# 3) Contain's different content
# OR
# 2) Exists in differnt place
def compare_dirs(base_dir, comp_dir):
    diff = {
        "DNE": {"unique_base": [], "unique_local": []},
        "DIFF": [],
        "DUPLICATE": {},
    }
    base_files = {}
    comp_files = {}

    # Go through base (Git) and compare to comp (local)
    for dirpath, dirnames, filenames in os.walk(base_dir):
        # Modify dirnames in place so os.walk doesn't traverse hidden dirs
        dirnames[:] = [dir for dir in dirnames if dir not in IGNORE_DIRS]

        # Get absolute path to both dirs
        abs_base_dir_path = os.path.normpath(os.path.abspath(dirpath))
        abs_comp_dir_path = os.path.abspath(
            os.path.join(comp_dir, os.path.basename(dirpath))
        )
        # Ensure dir references (., ..) are not included in path
        if os.path.basename(dirpath) == os.path.basename(base_dir):
            abs_comp_dir_path = os.path.abspath(comp_dir)
        logging.info(f"Base dir: {abs_base_dir_path}")
        logging.info(f"Comp dir: {abs_comp_dir_path}")

        # Iterate over files in base dir and check against comp dir
        for filename in filenames:
            base_file_path = os.path.join(abs_base_dir_path, filename)
            comp_file_path = os.path.join(abs_comp_dir_path, filename)
            logging.info(f"\tBase File: {base_file_path}")
            logging.info(f"\tComp File: {comp_file_path}")

            # Add files to base_files for tracking duplicates and diff filepaths
            if not base_files.get(filename):
                base_files[filename] = [base_file_path]
            else:
                base_files[filename].append(base_file_path)

            # Check if comp with same path exits
            if not os.path.exists(comp_file_path):
                diff["DNE"]["unique_base"].append(base_file_path)
                logging.info(f"\tISSUE: Comp file DNE\n")
            # Check if files with same path have same contents
            elif not filecmp.cmp(base_file_path, comp_file_path, shallow=False):
                with open(base_file_path) as base:
                    base_content = base.readlines()
                with open(comp_file_path) as comp:
                    comp_content = comp.readlines()

                diff_log = list(
                    difflib.unified_diff(
                        base_content, comp_content, base_file_path, comp_file_path
                    )
                )
                diff["DIFF"].append(diff_log)
                logging.info(f"\tISSUE: File contents differ\n")
            else:
                logging.info(f"\tMATCH\n")

    # Go through comp dirs and compare to base dirs
    for dirpath, dirnames, filenames in os.walk(comp_dir):
        # Modify dirnames in place so os.walk doesn't traverse hidden dirs
        dirnames[:] = [dir for dir in dirnames if dir not in IGNORE_DIRS]

        # Get absolute path to both dirs
        abs_comp_dir_path = os.path.abspath(os.path.abspath(dirpath))
        abs_base_dir_path = os.path.abspath(
            os.path.join(base_dir, os.path.basename(dirpath))
        )
        logging.info(f"Base dir: {abs_base_dir_path}")
        logging.info(f"Comp dir: {abs_comp_dir_path}")

        for filename in filenames:
            comp_file_path = os.path.join(abs_comp_dir_path, filename)
            base_file_path = os.path.join(abs_base_dir_path, filename)
            logging.info(f"\tBase File: {base_file_path}")
            logging.info(f"\tComp File: {comp_file_path}")

            # Add files to comp_files for tracking duplicates and diff filepaths
            comp_files.setdefault(filename, []).append(comp_file_path)

            # Check if base file with same path exists
            if not os.path.exists(base_file_path):
                diff["DNE"]["unique_local"].append(comp_file_path)
                logging.info(f"\tISSUE: Base file DNE\n")
            else:
                logging.info(f"\tMATCH\n")

    # Go over all base files and check for duplicates
    for base_file in base_files:
        # File is duplicated across base and comp with different paths
        if base_file in comp_files:
            base_paths = set(base_files[base_file])
            comp_paths = set(comp_files[base_file])

            # Same file appears in base and comp with different paths
            if base_paths != comp_paths:
                diff["DUPLICATE"].setdefault(base_file, []).extend(
                    base_files[base_file]
                )
                diff["DUPLICATE"].setdefault(base_file, []).extend(
                    comp_files[base_file]
                )
        # File not in comp, but duplicated in base
        elif len(base_files[base_file]) > 1:
            diff["DUPLICATE"].setdefault(base_file, []).extend(base_files[base_file])

    # Go over comp files and check for duplicates
    for comp_file in comp_files:
        if comp_files[comp_file] and len(comp_files[comp_file]) > 1:
            diff["DUPLICATE"].setdefault(comp_file, []).extend(comp_files[comp_file])

    # Print duplicates for logging
    for dup in diff["DUPLICATE"]:
        logging.info(f"Duplicate found: {dup}")
        for path in diff["DUPLICATE"][dup]:
            logging.info(f"\t{path}")
        logging.info("\n")

    if not diff:
        logging.info(f"No differences between base and local")

    return diff


def output_diff(diffs):
    # Create unique files using timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    with open(
        f"{OUTPUT_DIR_PATH}/missing/MISSING-{timestamp}.txt", "w", encoding="utf-8"
    ) as file:
        file.write("MISSING FILES:\nUNIQUE TO GIT:\n")
        for path in diffs["DNE"]["unique_base"]:
            file.write(make_link(path))

        file.write("UNIQUE TO LOCAL:\n")
        for path in diffs["DNE"]["unique_local"]:
            file.write(make_link(path))

    with open(f"{OUTPUT_DIR_PATH}/diff/DIFF-{timestamp}.txt", "w") as file:
        for diff in diffs["DIFF"]:
            file.writelines(diff)

    with open(
        f"{OUTPUT_DIR_PATH}/duplicate/DUPLICATE-{timestamp}.txt", "w", encoding="utf-8"
    ) as file:
        for dup in diffs["DUPLICATE"]:
            file.write(f"{dup}\n")
            for path in diffs["DUPLICATE"][dup]:
                file.write(make_link(path))


def print_dir_tree():
    for dirpath, dirnames, filenames in os.walk(PATH_A):
        # Modify dirnames in place so os.walk doesn't traverse hidden dirs
        dirnames[:] = [dir for dir in dirnames if dir not in IGNORE_DIRS]

        # Calculate depth and print dir
        depth = dirpath.replace(PATH_A, "").count(os.sep)
        print(f"{"\t" * depth}{os.path.normpath(dirpath)}")

        # Print files in dir
        for name in filenames:
            print(f"{"\t" * (depth + 1)}{name}")


def make_link(path):
    encoded_path = quote(path.replace("\\", "/"))
    return f"\t{path}\n\t→ [Open](" + f"file:///{encoded_path})\n\n"


def test():
    setup_logging(f"{OUTPUT_DIR_PATH}/log.txt")
    dirA = DirIndex("dirA")
    dirB = DirIndex("dirB")
    dirA.index_dir(PATH_A)
    dirB.index_dir(PATH_B)

    compare = dirA.compare_to(dirB)
    logging.info(compare["DUP"])
    logging.info(compare["DNE"])
    logging.info(compare["DIFF"])


def indexing_method():
    setup_logging(f"{OUTPUT_DIR_PATH}/log.txt")
    dirA = DirIndex("dirA")
    dirB = DirIndex("dirB")
    dirA.index_dir(PATH_B)
    dirB.index_dir(PATH_A)
    logging.info(dirA)
    logging.info(dirB)

    dirA_dup = dirA.find_self_duplicates()
    logging.info(dirA_dup)

    dirB_dup = dirB.find_self_duplicates()
    logging.info(dirB_dup)

    cross_dup = dirA.find_cross_duplicates(dirB)
    logging.info(cross_dup)

    dneA = dirA.find_DNE(dirB)
    logging.info(dneA)
    dneB = dirB.find_DNE(dirA)
    logging.info(dneB)

    cross_dif = dirA.find_diff(dirB)
    logging.info(cross_dif)


def old_method():
    setup_logging(f"{OUTPUT_DIR_PATH}/log.txt")
    diff = compare_dirs(PATH_A, PATH_B)
    output_diff(diff)


# Compare base_dir and new_dir and identify differences
if __name__ == "__main__":
    test()
