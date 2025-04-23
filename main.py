from log_config import setup_logging
from utils import write_compare_to_file
from dir_index import DirIndex
from dir_builder import UnionBuilder

from config import PATH_A, PATH_B, OUTPUT_DIR_PATH


def test_indexing():
    setup_logging(f"{OUTPUT_DIR_PATH}/log.txt")
    dirA = DirIndex("dirA")
    dirB = DirIndex("dirB")
    dirA.index_dir(PATH_A)
    dirB.index_dir(PATH_B)

    compare = dirA.compare_to(dirB)
    write_compare_to_file(compare)


def test_build():
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
    test_build()
