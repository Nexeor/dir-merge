import hashlib

from pathlib import Path
from comparison import Comparison, ComparisonResult


class File:
    def __init__(self, base_path: Path, abs_path: Path):
        self.name = abs_path.name
        self.rel_path = abs_path.relative_to(base_path)
        self.dir_path = abs_path.parent
        self.abs_path = abs_path
        self.size = abs_path.stat().st_size
        self.quick_hash = None
        self.full_hash = None

    def __repr__(self):
        return (
            f"File(name={self.name!r}, rel_path={self.rel_path!r}, size={self.size}, "
            f"quick_hash={self.quick_hash!r}, full_hash={self.full_hash!r})"
        )

    def __str__(self):
        msg = [
            f"File: {self.name}",
            f"\tRel_Path: {self.rel_path}",
            f"\tAbs_Path: {self.abs_path}",
            f"\tSize: {self.size}",
        ]
        if self.quick_hash is not None:
            msg.append(f"\tQuick Hash: {self.quick_hash}")
        if self.full_hash is not None:
            msg.append(f"\tFull Hash: {self.full_hash}")

        return "\n".join(msg)

    def compare_to(self, other: "File") -> Comparison:
        if self is other:
            raise ValueError(f"Attempted to compare file {repr(self)} to itself")

        # Compare traits
        same_name = self.name == other.name
        same_path = self.rel_path == other.rel_path
        same_content = self.compare_content(other)

        # Assign comparison type
        if same_name and same_path and same_content:
            return Comparison(self, other, ComparisonResult.MATCH)
        if same_name and same_path and not same_content:
            return Comparison(self, other, ComparisonResult.DIFF)
        if same_content and same_name and not same_path:
            return Comparison(self, other, ComparisonResult.CONTENT_NAME_DUP)
        if same_content and same_path and not same_name:
            return Comparison(self, other, ComparisonResult.CONTENT_PATH_DUP)
        if same_name and not same_path and not same_content:
            return Comparison(self, other, ComparisonResult.NAME_DUP)
        if same_content and not same_path and not same_name:
            return Comparison(self, other, ComparisonResult.CONTENT_DUP)
        return Comparison(self, other, ComparisonResult.UNIQUE)

    def compare_content(self, other: "File"):
        # Quick size check
        if self.size != other.size:
            return False

        # Quick hash comparison (about 4KB)
        if not self.quick_hash:
            self.quick_hash = self.__create_quick_hash()
        if not other.quick_hash:
            other.quick_hash = other.__create_quick_hash()
        if self.quick_hash != other.quick_hash:
            return False

        # Full hash comparison
        if not self.full_hash:
            self.full_hash = self.__create_full_hash()
        if not other.full_hash:
            other.full_hash = other.__create_full_hash()
        if self.full_hash != other.full_hash:
            return False

        return self.full_hash == other.full_hash

    def __create_quick_hash(self, chunk_size=4096):
        with open(self.abs_path, "rb") as file:
            fingerprint = file.read(chunk_size)
        return hashlib.md5(fingerprint).hexdigest()

    def __create_full_hash(self, algorithm="sha256", chunk_size=8192):
        hasher = hashlib.new(algorithm)
        with open(self.abs_path, "rb") as file:
            while chunk := file.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
