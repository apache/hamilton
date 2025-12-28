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

from __future__ import annotations

import argparse
import logging
import pathlib
from typing import Sequence

import nbformat

logger = logging.getLogger(__name__)

IGNORE_PRAGMA = "## ignore_ci"
EXCLUDED_EXAMPLES = []  # "model_examples/", )

SUCCESS = 0
FAILURE = 1


def _create_github_badge(path: pathlib.Path) -> str:
    github_url = f"https://github.com/apache/hamilton/blob/main/{path}"
    github_badge = f"[![GitHub badge](https://img.shields.io/badge/github-view_source-2b3137?logo=github)]({github_url})"
    return github_badge


def _create_colab_badge(path: pathlib.Path) -> str:
    colab_url = f"https://colab.research.google.com/github/dagworks-inc/hamilton/blob/main/{path}"
    colab_badge = (
        f"[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({colab_url})"
    )
    return colab_badge


def validate_notebook(notebook_path: pathlib.Path) -> int:
    """Check that the first code cell install dependencies for the notebook to work
    in Google Colab, and that the second cell has badges to open the notebook in
    Google Colab and view the source on GitHub.

    This function handles notebooks with or without Apache license headers:
    - If first cell is Apache license (markdown): check cells 2 and 3
    - Otherwise: check cells 1 and 2 (original behavior)

    NOTE. For faster notebook startup (especially on Colab), we should disable
    plugin autoloading

    .. code-block:: python

        #%% CELL_1 (optional)
        # Apache License header (markdown)

        #%% CELL_2 (or CELL_1 if no license)
        # Execute this cell to install dependencies
        %pip install sf-hamilton[visualization] matplotlib

        #%% CELL_3 (or CELL_2 if no license)
        # Title of the notebook ![Colab badge](colab_url) ![GitHub badge](github_url)

    """
    RETURN_VALUE = SUCCESS

    try:
        notebook = nbformat.read(notebook_path, as_version=4)
    except Exception as e:
        print(f"{notebook_path}: {e}")
        return FAILURE

    first_cell = notebook.cells[0]

    issues = []

    # if the ignore pragma is in the first cell, don't check other conditions
    if IGNORE_PRAGMA in first_cell.source:
        logger.info(f"Ignoring because path is excluded: `{notebook_path}`")
        return SUCCESS

    # Check if the first cell is an Apache license header
    has_license_header = (
        first_cell.cell_type == "markdown" and "Apache License" in first_cell.source
    )

    # Determine which cells to check based on whether there's a license header
    if has_license_header:
        # License header present: check cells 2 and 3 (indices 1 and 2)
        setup_cell = notebook.cells[1] if len(notebook.cells) > 1 else None
        title_cell = notebook.cells[2] if len(notebook.cells) > 2 else None
    else:
        # No license header: check cells 1 and 2 (indices 0 and 1) - original behavior
        setup_cell = first_cell
        title_cell = notebook.cells[1] if len(notebook.cells) > 1 else None

    # Validate setup cell
    if setup_cell is None:
        issues.append("Notebook must have at least a setup cell.")
        RETURN_VALUE |= FAILURE
    else:
        if setup_cell.cell_type != "code":
            issues.append("The setup cell should be a code cell.")
            RETURN_VALUE |= FAILURE

        if "%pip install" not in setup_cell.source:
            issues.append(
                "In the setup cell, use the `%pip` magic to install dependencies for the notebook."
            )
            RETURN_VALUE |= FAILURE

    # Validate title cell
    if title_cell is None:
        issues.append("Notebook must have a title cell.")
        RETURN_VALUE |= FAILURE
    else:
        if title_cell.cell_type != "markdown":
            issues.append(
                "The title cell should be markdown with the title, badges, and introduction."
            )
            RETURN_VALUE |= FAILURE

        if _create_colab_badge(notebook_path) not in title_cell.source:
            issues.append("Missing badge to open notebook in Google Colab.")
            RETURN_VALUE |= FAILURE

        if _create_github_badge(notebook_path) not in title_cell.source:
            issues.append("Missing badge to view source on GitHub.")
            RETURN_VALUE |= FAILURE

    if RETURN_VALUE == FAILURE:
        joined_issues = "\n\t".join(issues)
        print(f"{notebook_path}:\n\t{joined_issues}")

    return RETURN_VALUE


def insert_setup_cell(path: pathlib.Path):
    """Insert a setup cell at the top of a notebook (or after license header if present).

    Calling this multiple times will add multiple setup cells.

    This should be called before adding badges to the title cell,
    which is expected to be markdown.

    If the first cell is an Apache license header (markdown), the setup cell
    is inserted at position 1 (after the license). Otherwise, it's inserted at position 0.
    """
    notebook = nbformat.read(path, as_version=4)
    setup_cell = nbformat.v4.new_code_cell(
        "# Execute this cell to install dependencies\n%pip install sf-hamilton[visualization]"
    )

    # Check if first cell is a license header
    first_cell = notebook.cells[0] if len(notebook.cells) > 0 else None
    has_license_header = (
        first_cell is not None
        and first_cell.cell_type == "markdown"
        and "Apache License" in first_cell.source
    )

    # Insert after license header if present, otherwise at the beginning
    insert_position = 1 if has_license_header else 0
    notebook.cells.insert(insert_position, setup_cell)

    # cleanup required to avoid nbformat warnings
    for cell in notebook.cells:
        if "id" in cell:
            del cell["id"]

    nbformat.write(notebook, path)


def add_badges_to_title(path: pathlib.Path):
    """Add badges to the title cell of the notebook.

    This should be called after inserting the setup cell.

    The title cell is expected to be:
    - Cell 2 (index 2) if there's a license header at cell 0
    - Cell 1 (index 1) if there's no license header
    """

    notebook = nbformat.read(path, as_version=4)

    # Check if first cell is a license header
    first_cell = notebook.cells[0] if len(notebook.cells) > 0 else None
    has_license_header = (
        first_cell is not None
        and first_cell.cell_type == "markdown"
        and "Apache License" in first_cell.source
    )

    # Determine which cell is the title cell
    title_cell_index = 2 if has_license_header else 1

    if len(notebook.cells) <= title_cell_index:
        return

    if notebook.cells[title_cell_index].cell_type != "markdown":
        return

    updated_content = ""
    for idx, line in enumerate(notebook.cells[title_cell_index].source.splitlines()):
        if idx == 0:
            updated_content += f"{line} {_create_colab_badge(path)} {_create_github_badge(path)}\n"
        else:
            updated_content += f"\n{line}"

    notebook.cells[title_cell_index].update(source=updated_content)
    nbformat.write(notebook, path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*", type=pathlib.Path)
    args = parser.parse_args(argv)

    RETURN_VALUE = SUCCESS
    for filename in args.filenames:
        if any(filename.is_relative_to(excluded) for excluded in EXCLUDED_EXAMPLES):
            logger.info(f"Ignoring because path is excluded: `{filename}`")
            continue

        RETURN_VALUE |= validate_notebook(filename)

    return RETURN_VALUE


if __name__ == "__main__":
    raise SystemExit(main())
