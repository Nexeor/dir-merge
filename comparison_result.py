from enum import Enum


class ComparisonResult(Enum):
    MATCH = 0  # Same path, name, and content
    DIFF = 1  # Same path and name, different content
    CONTENT_NAME_DUP = 2  # Same content and name, different path
    CONTENT_PATH_DUP = 3  # Same content and path, different name
    NAME_DUP = 4  # Same name, different content and path
    CONTENT_DUP = 5  # Same content, different name and path
    UNIQUE = 6  # Content and name are different (path may be shared)
