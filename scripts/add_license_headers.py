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

"""Script to add Apache 2 license headers to files in the Hamilton repository."""

import json
import sys
from pathlib import Path
from typing import List

# TODO: Simplify this script if we add more file types. Since the license text
# (including line breaks) stays the same, we really just need different comment
# character insertion helpers based on file extension rather than duplicating
# the full license text for each file type.

# Apache 2 license header for Python files
PYTHON_LICENSE_HEADER = """# Licensed to the Apache Software Foundation (ASF) under one
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

"""

# Apache 2 license header for Markdown files (using HTML comments)
MARKDOWN_LICENSE_HEADER = """<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->

"""

# Apache 2 license header text for Jupyter notebooks (as markdown cell content)
NOTEBOOK_LICENSE_TEXT = """Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License."""

# Apache 2 license header for SQL files (using -- comments)
SQL_LICENSE_HEADER = """-- Licensed to the Apache Software Foundation (ASF) under one
-- or more contributor license agreements.  See the NOTICE file
-- distributed with this work for additional information
-- regarding copyright ownership.  The ASF licenses this file
-- to you under the Apache License, Version 2.0 (the
-- "License"); you may not use this file except in compliance
-- with the License.  You may obtain a copy of the License at
--
--   http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing,
-- software distributed under the License is distributed on an
-- "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
-- KIND, either express or implied.  See the License for the
-- specific language governing permissions and limitations
-- under the License.

"""


def add_license_to_python(content: str) -> str:
    """Add Apache 2 license header to Python file content."""
    # Handle shebang lines - preserve them at the top
    lines = content.split("\n", 1)
    if lines[0].startswith("#!"):
        # File has shebang, add license after it
        if len(lines) > 1:
            return lines[0] + "\n" + PYTHON_LICENSE_HEADER + lines[1]
        else:
            return lines[0] + "\n" + PYTHON_LICENSE_HEADER
    else:
        # No shebang, add license at the beginning
        return PYTHON_LICENSE_HEADER + content


def add_license_to_markdown(content: str) -> str:
    """Add Apache 2 license header to Markdown file content."""
    return MARKDOWN_LICENSE_HEADER + content


def add_license_to_notebook(content: str) -> str:
    """Add Apache 2 license header to Jupyter notebook."""
    try:
        notebook = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid notebook JSON: {e}") from e

    # Create a new markdown cell with the license
    license_cell = {"cell_type": "markdown", "metadata": {}, "source": [NOTEBOOK_LICENSE_TEXT]}

    # Insert at the beginning
    if "cells" not in notebook:
        notebook["cells"] = []

    notebook["cells"].insert(0, license_cell)

    return json.dumps(notebook, indent=1, ensure_ascii=False)


def add_license_to_shell(content: str) -> str:
    """Add Apache 2 license header to shell script or Dockerfile.

    Uses same logic as Python files (# comments, handle shebang).
    """
    # Handle shebang lines - preserve them at the top
    lines = content.split("\n", 1)
    if lines[0].startswith("#!"):
        # File has shebang, add license after it
        if len(lines) > 1:
            return lines[0] + "\n" + PYTHON_LICENSE_HEADER + lines[1]
        else:
            return lines[0] + "\n" + PYTHON_LICENSE_HEADER
    else:
        # No shebang, add license at the beginning
        return PYTHON_LICENSE_HEADER + content


def add_license_to_sql(content: str) -> str:
    """Add Apache 2 license header to SQL file content."""
    return SQL_LICENSE_HEADER + content


def add_license_header(file_path: Path, dry_run: bool = False) -> bool:
    """Add Apache 2 license header to a file.

    Args:
        file_path: Path to the file
        dry_run: If True, only print what would be done without modifying files

    Returns:
        True if header was added (or would be added in dry run), False otherwise
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, PermissionError) as e:
        print(f"  ✗ Error reading {file_path}: {e}")
        return False

    # Check if file already has a license header (check first 20 lines only)
    first_lines = "\n".join(content.split("\n")[:20])
    if (
        "Licensed to the Apache Software Foundation" in first_lines
        or "Apache License" in first_lines
    ):
        print(f"  ↷ Skipping {file_path} (already has license header)")
        return False

    # Determine file type and add appropriate header
    try:
        if file_path.suffix == ".py":
            new_content = add_license_to_python(content)
        elif file_path.suffix == ".md":
            new_content = add_license_to_markdown(content)
        elif file_path.suffix == ".ipynb":
            new_content = add_license_to_notebook(content)
        elif file_path.suffix == ".sh":
            new_content = add_license_to_shell(content)
        elif file_path.suffix == ".sql":
            new_content = add_license_to_sql(content)
        elif file_path.name == "Dockerfile":
            # Dockerfiles use # comments like shell scripts
            new_content = add_license_to_shell(content)
        elif file_path.name == "README":
            # README files without extension are usually markdown
            new_content = add_license_to_markdown(content)
        else:
            print(f"  ✗ Unsupported file type: {file_path.suffix} ({file_path.name})")
            return False
    except Exception as e:
        print(f"  ✗ Error processing {file_path}: {e}")
        return False

    if dry_run:
        print(f"  ✓ Would add license header to {file_path}")
        return True

    # Write the modified content back
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"  ✓ Added license header to {file_path}")
        return True
    except (PermissionError, OSError) as e:
        print(f"  ✗ Error writing {file_path}: {e}")
        return False


def main():
    """Main function."""
    # Get repository root (parent of scripts directory)
    repo_root = Path(__file__).parent.parent

    # Check for dry-run flag
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv

    if dry_run:
        print("DRY RUN MODE - No files will be modified\n")

    # Read the list of files from command line or use default
    if len(sys.argv) > 1 and not sys.argv[-1].startswith("-"):
        list_file = repo_root / sys.argv[-1]
    else:
        # Try combined list first, fall back to missing_license_headers.txt
        list_file = repo_root / "missing_license_headers_combined.txt"
        if not list_file.exists():
            list_file = repo_root / "missing_license_headers.txt"

    if not list_file.exists():
        print(f"Error: {list_file} not found!")
        print("Run check_license_headers.py first to generate the list.")
        print("Or specify a file list: python add_license_headers.py <file_list>")
        return 1

    print(f"Using file list: {list_file.name}\n")

    # Parse the file list
    files_to_update: List[Path] = []
    with open(list_file, "r") as f:
        for line in f:
            original_line = line
            line = line.strip()
            # Skip header lines and empty lines
            if (
                not line
                or line.startswith("Checking")
                or line.startswith("Extensions")
                or line.startswith("Found")
            ):
                continue
            # Skip lines that look like section headers (not starting with space and not a file path)
            if (
                not original_line.startswith(" ")
                and not line.startswith("examples")
                and not line.startswith("hamilton")
                and "/" not in line
            ):
                continue
            # Remove leading spaces
            file_path = line
            full_path = repo_root / file_path
            if full_path.exists():
                files_to_update.append(full_path)

    if not files_to_update:
        print("No files to update!")
        return 0

    print(f"Found {len(files_to_update)} files to add license headers to\n")

    # Process each file
    success_count = 0
    skip_count = 0

    for file_path in files_to_update:
        result = add_license_header(file_path, dry_run=dry_run)
        if result:
            success_count += 1
        else:
            # Could be a skip or an error - check the output
            skip_count += 1

    # Print summary
    print(f"\n{'Would add' if dry_run else 'Added'} license headers to {success_count} files")
    if skip_count > 0:
        print(f"Skipped {skip_count} files")

    return 0


if __name__ == "__main__":
    sys.exit(main())
