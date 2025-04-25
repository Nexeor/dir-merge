import hashlib

from collections import defaultdict
from pathlib import Path
from enum import Enum


class File:
    def __init__(self, abs_path=Path):
        self.name = abs_path.name
        self.path = abs_path.parent
        self.size = abs_path.stat().st_size
        self.quick_hash = None
        self.full_hash = None

    def __str__(self):
        return (
            f"File: {self.name}\n"
            f"\tPath: {self.path}\n"
            f"\tSize: {self.size}\n"
            f"\tHash: {self.hash}"
        )

    def compare(self, other: "File"):
        # Check basics
        same_name = self.name == other.name
        same_path = self.path == other.path

        # Content compare
        same_content = self.compare_content(other)

    def compare_content(self, other: "File"):
        # Quick size check
        if self.size == other.size:
            # Ensure the files have been quick hashed
            self.quick_hash = self.quick_hash or self.__create_quick_hash()
            other.quick_hash = other.quick_hash or other.__create_quick_hash()

            if self.quick_hash == other.quick_hash:
                # Ensure the files have been fully hashed
                self.full_hash = self.full_hash or self.__create_full_hash()
                other.full_hash = other.full_hash or other.__create_full_hash()

                if self.full_hash == other.full_hash:
                    return True
        return False

    # Given two file paths, check if they contain the same content
    def check_file_diff(file_path_A, file_path_B):
        diff_log = None
        if not filecmp.cmp(file_path_A, file_path_B, shallow=False):
            with open(file_path_A) as base:
                base_content = base.readlines()
            with open(file_path_B) as comp:
                comp_content = comp.readlines()

            diff_log = list(
                difflib.unified_diff(
                    base_content, comp_content, file_path_A, file_path_B
                )
            )
        return diff_log

    def __create_quick_hash(self, chunk_size=4096):
        with open(self.path, "rb") as file:
            fingerprint = file.read(chunk_size)
        return hashlib.md5(fingerprint).hexdigest()

    def __create_full_hash(self, algorithm="sha256", chunk_size=8192):
        hasher = hashlib.new(algorithm)
        with open(self.path, "rb") as file:
            while chunk := file.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()


class ComparisonRes(Enum):
    MATCH = "match"
    DIFF = "diff"
    CONTENT_NAME_DUP = "content-name dup"
    CONTENT_PATH_DUP = "content-path dup"
    NAME_DUP = "name dup"
    CONTENT_DUP = "content dup"
    UNIQUE = "unique"
