import hashlib
from pathlib import Path

from utils import make_link
from comparison import Comparison, CompType


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
            f"\tRelative Path: {self.rel_path}",
            f"\tSize: {self.size}",
            f"\tView File: {make_link(self.abs_path)}",
        ]

        return "\n".join(msg)

    def compare_to(self, other: "File") -> Comparison:
        if self is other:
            raise ValueError(f"Attempted to compare file {repr(self)} to itself")

        # Compare traits
        same_name = self.name == other.name
        same_path = self.rel_path.parent == other.rel_path.parent
        same_content = self.compare_content(other)

        # Assign comparison type
        for comp_type in CompType:
            traits = comp_type.value
            if (
                traits["path"] == same_path
                and traits["name"] == same_name
                and traits["content"] == same_content
            ):
                return Comparison(self, other, comp_type)
        raise ValueError(
            f"No valid CompType found for comparison between {repr(self)} and {repr(other)}"
        )

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
