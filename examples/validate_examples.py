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
    github_url = f"https://github.com/dagworks-inc/hamilton/blob/main/{path}"
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

    NOTE. For faster notebook startup (especially on Colab), we should disable
    plugin autoloading

    .. code-block:: python

        #%% CELL_1
        # Execute this cell to install dependencies
        %pip install sf-hamilton[visualization] matplotlib

        #%% CELL_2
        # Title of the notebook ![Colab badge](colab_url) ![GitHub badge](github_url)

    """
    RETURN_VALUE = SUCCESS

    try:
        notebook = nbformat.read(notebook_path, as_version=4)
    except Exception as e:
        print(f"{notebook_path}: {e}")
        return FAILURE

    first_cell = notebook.cells[0]
    second_cell = notebook.cells[1]

    issues = []

    # if the ignore pragma is in the first cell, don't check other conditions
    if IGNORE_PRAGMA in first_cell.source:
        logger.info(f"Ignoring because path is excluded: `{notebook_path}`")
        return SUCCESS

    if first_cell.cell_type != "code":
        issues.append("The first cell should be a code cell to set up the notebook.")
        RETURN_VALUE |= FAILURE

    if "%pip install" not in first_cell.source:
        issues.append(
            "In the first cell, use the `%pip` magic to install dependencies for the notebook."
        )
        RETURN_VALUE |= FAILURE

    if second_cell.cell_type != "markdown":
        issues.append(
            "The second cell should be markdown with the title, badges, and introduction."
        )
        RETURN_VALUE |= FAILURE

    if _create_colab_badge(notebook_path) not in second_cell.source:
        issues.append("Missing badge to open notebook in Google Colab.")
        RETURN_VALUE |= FAILURE

    if _create_github_badge(notebook_path) not in second_cell.source:
        issues.append("Missing badge to view source on GitHub.")
        RETURN_VALUE |= FAILURE

    if RETURN_VALUE == FAILURE:
        joined_issues = "\n\t".join(issues)
        print(f"{notebook_path}:\n\t{joined_issues}")

    return RETURN_VALUE


def insert_setup_cell(path: pathlib.Path):
    """Insert a setup cell at the top of a notebook.

    Calling this multiple times will add multiple setup cells.

    This should be called before adding badges to the second cell,
    which is expected to be markdown.
    """
    notebook = nbformat.read(path, as_version=4)
    setup_cell = nbformat.v4.new_code_cell(
        "# Execute this cell to install dependencies\n%pip install sf-hamilton[visualization]"
    )
    notebook.cells.insert(0, setup_cell)

    # cleanup required to avoid nbformat warnings
    for cell in notebook.cells:
        if "id" in cell:
            del cell["id"]

    nbformat.write(notebook, path)


def add_badges_to_title(path: pathlib.Path):
    """Add badges to the second cell of the notebook.

    This should be called after inserting the setup cell,
    which should be the first cell of the notebook.
    """

    notebook = nbformat.read(path, as_version=4)
    if notebook.cells[1].cell_type != "markdown":
        return

    updated_content = ""
    for idx, line in enumerate(notebook.cells[1].source.splitlines()):
        if idx == 0:
            updated_content += f"{line} {_create_colab_badge(path)} {_create_github_badge(path)}\n"
        else:
            updated_content += f"\n{line}"

    notebook.cells[1].update(source=updated_content)
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
