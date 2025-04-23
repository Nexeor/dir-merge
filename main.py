import argparse

from log_config import setup_logging
from utils import write_compare_to_file
from dir_index import DirIndex
from dir_builder import UnionBuilder

from config import PATH_A, PATH_B, OUTPUT_DIR_PATH


def main():
    setup_logging
    args = parse_args()
    if args.index:
        build_index()
    elif args.combine:
        build_union()
    else:
        build_union()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--index", action="store_true")
    parser.add_argument("-u", "--union", action="store_true")

    return parser.parse_args()


def build_index():
    setup_logging(f"{OUTPUT_DIR_PATH}/log.txt")
    dirA = DirIndex("dirA")
    dirB = DirIndex("dirB")
    dirA.index_dir(PATH_A)
    dirB.index_dir(PATH_B)

    compare = dirA.compare_to(dirB)
    write_compare_to_file(compare)


def build_union():
    setup_logging(f"{OUTPUT_DIR_PATH}/log.txt")
    dirA = DirIndex("dirA")
    dirB = DirIndex("dirB")
    dirA.index_dir(PATH_A)
    dirB.index_dir(PATH_B)

    compare = dirA.compare_to(dirB)
    union = UnionBuilder()
    union.add_matches(compare["MATCH"])


# Compare base_dir and new_dir and identify differences
if __name__ == "__main__":
    main()
