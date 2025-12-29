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
from typing import List

# License header patterns to check for
# ASF-specific header (our standard)
ASF_LICENSE_PATTERNS = [
    "Licensed to the Apache Software Foundation (ASF)",
    "Apache License, Version 2.0",
]

# Third-party Apache 2.0 headers (also acceptable)
# Note: Some third-party headers may have spaces in the URL
THIRD_PARTY_APACHE_PATTERNS = [
    "Apache License, Version 2.0",
    "www.apache.org/licenses/LICENSE-2.0",
]

# File extensions to EXCLUDE from checking (based on what exists in this repo)
EXCLUDED_EXTENSIONS = {
    # Python compiled/generated
    ".pyc",
    ".pyi",  # Type stubs
    ".pyx",  # Cython
    ".pxd",  # Cython headers
    ".pxi",  # Cython includes
    # Compiled binaries
    ".so",
    ".dylib",
    ".jar",
    # Images and media
    ".png",
    ".svg",
    ".ttf",
    ".afm",  # Adobe font metrics
    # Config/data files
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".toml",
    ".cfg",  # setup.cfg, etc.
    ".conf",  # nginx.conf, etc.
    ".xml",  # Test data, config files
    ".csv",
    ".fwf",  # Fixed-width format test data
    ".dot",  # Graphviz DOT files
    ".npy",  # NumPy arrays
    ".mat",  # MATLAB data
    ".sav",  # SPSS data
    ".po",  # Gettext translations
    ".mo",  # Compiled translations
    ".template",  # Template config files
    # Build/generated files
    ".map",  # Source maps
    ".gz",
    ".log",
    ".typed",  # PEP 561 marker
    # Web assets (usually don't have license headers)
    ".css",
    ".scss",
    ".html",
    # JavaScript config files (these are code but often generated)
    ".eslintrc",
    ".nycrc",
    ".npmignore",
    ".editorconfig",
    # Template files
    ".j2",
    ".jinja2",
    # Documentation that doesn't need headers
    ".txt",
    ".rst",
    # Other
    ".gitkeep",
    ".asc",  # GPG keys
    ".cmd",  # Windows batch
    ".coffee",  # CoffeeScript (if any)
    ".mjs",  # ES modules (often generated)
    ".cjs",  # CommonJS modules (often generated)
    ".mts",  # TypeScript ES modules
    ".flow",  # Flow type definitions
    ".in",  # MANIFEST.in, etc.
}

# Specific filenames to exclude (exact matches)
EXCLUDED_FILENAMES = {
    # Lock files
    "package-lock.json",
    "yarn.lock",
    "poetry.lock",
    "uv.lock",
    # License/legal files
    "LICENSE",
    "NOTICE",
    "CHANGELOG",
    # OS files
    ".DS_Store",
}

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
    """Check if a file has an Apache 2 license header (ASF or third-party)."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = "".join(f.readlines()[:num_lines])

        # Check if all ASF license patterns are present
        has_asf_header = all(pattern in content for pattern in ASF_LICENSE_PATTERNS)

        # Check if all third-party Apache 2.0 patterns are present
        has_third_party_header = all(pattern in content for pattern in THIRD_PARTY_APACHE_PATTERNS)

        # Accept either ASF or third-party Apache 2.0 headers
        return has_asf_header or has_third_party_header
    except (UnicodeDecodeError, PermissionError):
        # Skip files that can't be read as text
        return True  # Assume they're fine to avoid false positives


def find_files_without_license(root_dir: Path) -> List[Path]:
    """Find all files without Apache 2 license headers.

    Uses an exclusion-based approach: checks all files except those with
    excluded extensions or filenames.

    Args:
        root_dir: Root directory to search

    Returns:
        Sorted list of file paths without license headers
    """
    files_without_license = []

    for file_path in root_dir.rglob("*"):
        # Skip directories
        if file_path.is_dir():
            continue

        # Skip if in excluded paths
        if should_skip_path(file_path):
            continue

        # Skip if extension is in exclusion list
        if file_path.suffix in EXCLUDED_EXTENSIONS:
            continue

        # Skip if filename is in exclusion list
        if file_path.name in EXCLUDED_FILENAMES:
            continue

        # Skip editor backup files (emacs, vim, etc.)
        if (
            file_path.name.startswith("#")
            or file_path.name.endswith("~")
            or file_path.name.endswith("#")
        ):
            continue

        # Skip files without extensions that aren't special files
        if (
            not file_path.suffix
            and not file_path.name.startswith("Dockerfile")
            and file_path.name != "README"
        ):
            continue

        # Check for license header
        if not has_license_header(file_path):
            files_without_license.append(file_path)

    return sorted(files_without_license)


def main():
    """Main function."""
    # Get repository root (parent of scripts directory)
    repo_root = Path(__file__).parent.parent

    print(f"Checking for Apache 2 license headers in {repo_root}")
    print("Mode: Checking all files except excluded types")
    print(f"Excluded extensions: {len(EXCLUDED_EXTENSIONS)} types")
    print(f"Excluded filenames: {len(EXCLUDED_FILENAMES)} patterns")
    print()

    files_without_license = find_files_without_license(repo_root)

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
