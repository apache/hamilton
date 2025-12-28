#!/usr/bin/env python3
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Script to find files missing Apache 2 license headers in the Hamilton repository."""

import sys
from pathlib import Path
from typing import List, Set

# License header patterns to check for
LICENSE_PATTERNS = [
    "Licensed to the Apache Software Foundation (ASF)",
    "Apache License, Version 2.0",
]

# File extensions to check
PYTHON_EXTENSIONS = {".py"}
MARKDOWN_EXTENSIONS = {".md"}
NOTEBOOK_EXTENSIONS = {".ipynb"}
SHELL_EXTENSIONS = {".sh"}
SQL_EXTENSIONS = {".sql"}
TYPESCRIPT_EXTENSIONS = {".ts", ".tsx"}
JAVASCRIPT_EXTENSIONS = {".js", ".jsx"}
ALL_EXTENSIONS = (
    PYTHON_EXTENSIONS
    | MARKDOWN_EXTENSIONS
    | NOTEBOOK_EXTENSIONS
    | SHELL_EXTENSIONS
    | SQL_EXTENSIONS
    | TYPESCRIPT_EXTENSIONS
    | JAVASCRIPT_EXTENSIONS
)

# Directories to skip
SKIP_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "venv",
    ".venv",
    "build",
    "dist",
    "*.egg-info",
    ".eggs",
    "htmlcov",
    ".coverage",
    ".claude",
}


def should_skip_path(path: Path) -> bool:
    """Check if a path should be skipped."""
    # Skip if any parent directory is in SKIP_DIRS
    for part in path.parts:
        if part in SKIP_DIRS or part.startswith("."):
            return True

    # Skip documentation snippet files (they're embedded in docs via literalinclude)
    path_str = str(path)
    if "docs" in path.parts and "_snippets" in path_str:
        return True
    if "docs/code-comparisons" in path_str and "snippets" in path_str:
        return True

    return False


def has_license_header(file_path: Path, num_lines: int = 20) -> bool:
    """Check if a file has the Apache 2 license header."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = "".join(f.readlines()[:num_lines])

        # Check if all license patterns are present in the first N lines
        return all(pattern in content for pattern in LICENSE_PATTERNS)
    except (UnicodeDecodeError, PermissionError):
        # Skip files that can't be read as text
        return True  # Assume they're fine to avoid false positives


def find_files_without_license(
    root_dir: Path, extensions: Set[str] = ALL_EXTENSIONS, include_special: bool = True
) -> List[Path]:
    """Find all files without Apache 2 license headers.

    Args:
        root_dir: Root directory to search
        extensions: Set of file extensions to check
        include_special: Whether to include special files like Dockerfile and README (no extension)
    """
    files_without_license = []

    # Special files to check (by exact name, not extension)
    SPECIAL_FILES = {"Dockerfile", "README"}

    for file_path in root_dir.rglob("*"):
        # Skip directories
        if file_path.is_dir():
            continue

        # Check if file matches by extension or by special name
        matches_extension = file_path.suffix in extensions
        matches_special = include_special and file_path.name in SPECIAL_FILES

        if not (matches_extension or matches_special):
            continue

        # Skip if in excluded paths
        if should_skip_path(file_path):
            continue

        # Check for license header
        if not has_license_header(file_path):
            files_without_license.append(file_path)

    return sorted(files_without_license)


def main():
    """Main function."""
    # Get repository root (parent of scripts directory)
    repo_root = Path(__file__).parent.parent

    # Allow specifying extensions via command line
    if len(sys.argv) > 1:
        extension_arg = sys.argv[1]
        if extension_arg == "py":
            extensions = PYTHON_EXTENSIONS
        elif extension_arg == "md":
            extensions = MARKDOWN_EXTENSIONS
        elif extension_arg == "ipynb":
            extensions = NOTEBOOK_EXTENSIONS
        elif extension_arg == "sh":
            extensions = SHELL_EXTENSIONS
        elif extension_arg == "sql":
            extensions = SQL_EXTENSIONS
        elif extension_arg == "ts":
            extensions = TYPESCRIPT_EXTENSIONS
        elif extension_arg == "js":
            extensions = JAVASCRIPT_EXTENSIONS
        elif extension_arg == "special":
            # Check only Dockerfile and README files
            extensions = set()
        else:
            extensions = ALL_EXTENSIONS
    else:
        extensions = ALL_EXTENSIONS

    # Only include special files (Dockerfile, README) if checking all or "special" type
    include_special = len(sys.argv) <= 1 or (
        len(sys.argv) > 1 and sys.argv[1] in ["special", "all"]
    )

    print(f"Checking for Apache 2 license headers in {repo_root}")
    if extensions:
        print(f"Extensions: {', '.join(sorted(extensions))}")
    if include_special:
        print("Including: Dockerfile, README files")
    print()

    files_without_license = find_files_without_license(repo_root, extensions, include_special)

    if not files_without_license:
        print("✓ All files have license headers!")
        return 0

    print(f"Found {len(files_without_license)} files without Apache 2 license headers:\n")

    for file_path in files_without_license:
        # Print relative path from repo root
        try:
            rel_path = file_path.relative_to(repo_root)
            print(f"  {rel_path}")
        except ValueError:
            print(f"  {file_path}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
