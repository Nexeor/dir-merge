from enum import Enum
from file import File


class Comparison:
    class CompType(Enum):
        # Same path, name, and content
        MATCH = {"path": True, "name": True, "content": True}

        # Same path and name, different content
        PATH_NAME_DUP = {"path": True, "name": True, "content": False}
        # Same content and name, different path
        CONTENT_NAME_DUP = {"path": False, "name": True, "content": True}
        # Same content and path, different name
        CONTENT_PATH_DUP = {"path": True, "name": False, "content": True}

        # Same name, different content and path
        NAME_DUP = {"path": False, "name": True, "content": False}
        # Same content, different name and path
        CONTENT_DUP = {"path": False, "name": False, "content": True}

        # No shared traits
        UNIQUE = {"path": False, "name": False, "content": False}

    def __init__(self, fileA: File, fileB: File):
        self.fileA: File = fileA
        self.fileB: File = fileB
        self.comp_type: CompType = fileA.compare_to(fileB)

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


# Define alias
CompType = Comparison.CompType
