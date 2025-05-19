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

    def __init__(self, fileA, fileB):
        from file import File

        self.fileA: File = fileA
        self.fileB: File = fileB
        self.comp_type: CompType = self.compare_files(fileA, fileB)

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

    def compare_files(file_a: File, file_b: File) -> CompType:
        if file_a is file_b:
            raise ValueError(f"Attempted to compare file {repr(file_a)} to itself")

        # Compare traits
        same_name = file_a.name == file_b.name
        same_path = file_a.rel_path.parent == file_b.rel_path.parent
        same_content = file_a.compare_content(file_b)

        # Assign comparison type
        for comp_type in CompType:
            traits = comp_type.value
            if (
                traits["path"] == same_path
                and traits["name"] == same_name
                and traits["content"] == same_content
            ):
                return comp_type
        raise ValueError(
            f"No valid CompType found for comparison between {repr(file_a)} and {repr(file_b)}"
        )


# Define alias
CompType = Comparison.CompType
