import hashlib

from collections import defaultdict
from pathlib import Path


class File:
    def __init__(self, abs_path=Path):
        self.name = abs_path.name
        self.path = abs_path.parent
        self.size = abs_path.stat().st_size
        self.hash = self.__quick_hash(abs_path)

    def __str__(self):
        return (
            f"File: {self.name}\n"
            f"\tPath: {self.path}\n"
            f"\tSize: {self.size}\n"
            f"\tHash: {self.hash}"
        )

    def __quick_hash(self, filepath, chunk_size=4096):
        with open(filepath, "rb") as file:
            fingerprint = file.read(chunk_size)
        return hashlib.md5(fingerprint).hexdigest()
