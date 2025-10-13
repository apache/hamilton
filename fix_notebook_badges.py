#!/usr/bin/env python
"""Script to fix notebook badges by ensuring they use the exact format expected by the validation script."""

import nbformat
import pathlib
from examples.validate_examples import add_badges_to_title, insert_setup_cell


def fix_notebook_badges(notebook_path):
    """Fix badges in a single notebook."""
    path = pathlib.Path(notebook_path)
    print(f'Processing {notebook_path}...')
    
    try:
        # Add setup cell if needed (only if first cell is not code)
        with open(path, 'r', encoding='utf-8') as f:
            notebook = nbformat.read(f, as_version=4)
        
        if len(notebook.cells) > 0 and notebook.cells[0].cell_type != 'code':
            insert_setup_cell(path)
            print(f'  Added setup cell to {notebook_path}')
        
        # Always try to add badges in the correct format
        add_badges_to_title(path)
        print(f'  Added/updated badges in {notebook_path}')
        
    except Exception as e:
        print(f'  Error processing {notebook_path}: {e}')


if __name__ == "__main__":
    # Get all .ipynb files in examples directory
    notebook_paths = []
    for path in pathlib.Path("examples").rglob("*.ipynb"):
        notebook_paths.append(str(path))
    
    print(f"Found {len(notebook_paths)} notebooks to process")
    
    for notebook_path in notebook_paths:
        fix_notebook_badges(notebook_path)