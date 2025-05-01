from enum import Enum


class ComparisonResult(Enum):
    MATCH = ("path", "name", "content")  # Same path, name, and content
    DIFF = ("path", "name")  # Same path and name, different content
    CONTENT_NAME_DUP = ("content", "name")  # Same content and name, different path
    CONTENT_PATH_DUP = ("content", "path")  # Same content and path, different name
    NAME_DUP = ("name",)  # Same name, different content and path
    CONTENT_DUP = ("content",)  # Same content, different name and path
    UNQIUE = ()  # No shared traits


class Comparison:
    def __init__(self, fileA, fileB, type: ComparisonResult):
        self.fileA = fileA
        self.fileB = fileB
        self.type = type

    def __repr__(self):
        return (
            f"Comparison(type={self.type.name}, "
            f"fileA={repr(self.fileA)}, "
            f"fileB={repr(self.fileB)})"
        )

    def __str__(self):
        return (
            f"Comparison Type: {self.type.name}\n"
            f"File A: {self.fileA.name} ({self.fileA.rel_path})\n"
            f"File B: {self.fileB.name} ({self.fileB.rel_path})"
        )
