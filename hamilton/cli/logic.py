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

from pathlib import Path
from types import ModuleType

from hamilton import driver

CONFIG_HEADER = "HAMILTON_CONFIG"
FINAL_VARS_HEADER = "HAMILTON_FINAL_VARS"
INPUTS_HEADER = "HAMILTON_INPUTS"
OVERRIDES_HEADER = "HAMILTON_OVERRIDES"


def get_git_base_directory() -> str:
    """Get the base path of the current git directory"""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print("Error:", result.stderr.strip())
            raise OSError(f"{result.stderr.strip()}")
    except FileNotFoundError as e:
        raise FileNotFoundError("Git command not found. Please make sure Git is installed.") from e


def get_git_reference(git_relative_path: str | Path, git_reference: str) -> str:
    """Get the source code from the specified file and git reference"""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "show", f"{git_reference}:{git_relative_path}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode == 0:
            return result.stdout.strip()
        elif result.returncode == 128:
            # TODO catch the following error:
            # fatal: Path '{git_relative_path}' exists on disk, but not in '{git_revision}'.
            return
        else:
            return
    except FileNotFoundError as e:
        raise FileNotFoundError("Git command not found. Please make sure Git is installed.") from e


def version_hamilton_functions(module: ModuleType) -> dict[str, str]:
    """Hash the source code of Hamilton functions from a module"""
    from hamilton import graph_types, graph_utils

    origins_version: dict[str, str] = dict()

    for origin_name, _ in graph_utils.find_functions(module):
        origin_callable = getattr(module, origin_name)
        origins_version[origin_name] = graph_types.hash_source_code(origin_callable, strip=True)

    return origins_version


def hash_hamilton_nodes(dr: driver.Driver) -> dict[str, str]:
    """Hash the source code of Hamilton functions from nodes in a Driver"""
    from hamilton import graph_types

    graph = graph_types.HamiltonGraph.from_graph(dr.graph)
    return {n.name: n.version for n in graph.nodes}


def map_nodes_to_functions(dr: driver.Driver) -> dict[str, str]:
    """Get a mapping from node name to Hamilton function name"""
    from hamilton import graph_types

    graph = graph_types.HamiltonGraph.from_graph(dr.graph)

    node_to_function = dict()
    for n in graph.nodes:
        # is None for config nodes
        if n.originating_functions is None:
            continue

        node_callable = n.originating_functions[0]
        node_to_function[n.name] = node_callable.__name__

    return node_to_function


def hash_dataflow(nodes_version: dict[str, str]) -> str:
    """Create a dataflow hash from the hashes of its nodes"""
    import hashlib

    sorted_nodes = sorted(nodes_version.values())
    return hashlib.sha256(str(sorted_nodes).encode()).hexdigest()


def load_modules_from_git(
    module_paths: list[Path], git_reference: str = "HEAD"
) -> list[ModuleType]:
    """Dynamically import modules for a git reference"""
    from hamilton import ad_hoc_utils

    git_base_dir = Path(get_git_base_directory())

    modules = []
    for module_path in module_paths:
        relative_to_git = module_path.relative_to(git_base_dir)
        previous_revision = get_git_reference(relative_to_git, git_reference)
        module = ad_hoc_utils.module_from_source(previous_revision)
        modules.append(module)

    return modules


def diff_nodes_against_functions(
    nodes_version: dict[str, str],
    origins_version: dict[str, str],
    node_to_origin: dict[str, str],
) -> dict:
    """Compare the nodes version from a built Driver to
    the origins version from module source code when a second
    Driver can't be instantiated

    :nodes_version: mapping from node name to its origin function hash
    :origins_version: mapping from origin function name to origin function hash
    :node_to_origin: mapping from node name to origin name
    """
    node_added = []
    code_diff = []
    origins_removed = []

    # iterate over nodes from built Driver
    for node_name, node_version in nodes_version.items():
        origin_name = node_to_origin[node_name]
        origin_version = origins_version.get(origin_name)

        # if origin_version is None, the node is new
        if origin_version is None:
            node_added.append(node_name)
            continue

        # if node_version != origin_version, the current node's origin
        # function existed before, but was edited since origin_version
        if node_version != origin_version:
            code_diff.append(node_name)

    nodes_origin_version = set(nodes_version.values())
    # iterate over origin functions from source code
    for origin_name, origin_version in origins_version.items():
        # if origin_version not found in nodes_version, the
        # origin function is not used by the built Driver
        if origin_version not in nodes_origin_version:
            origins_removed.append(origin_name)

    return dict(
        nodes_added=node_added,
        code_diff=code_diff,
        origins_removed=origins_removed,
    )


def diff_versions(current_map: dict[str, str], reference_map: dict[str, str]) -> dict:
    """Generic diff of two {name: hash} mappings (can be node or origin name)

    :mapping_v1: mapping from node (or function) name to its function hash
    :mapping_v2: mapping from node (or function) name to its function hash
    """
    current_only, reference_only, edit = [], [], []

    for node_name, v1 in current_map.items():
        v2 = reference_map.get(node_name)
        if v2 is None:
            current_only.append(node_name)
            continue

        if v1 != v2:
            edit.append(node_name)

    for node_name, _ in reference_map.items():
        v1 = current_map.get(node_name)
        if v1 is None:
            reference_only.append(node_name)
            continue

    return dict(current_only=current_only, reference_only=reference_only, edit=edit)


def _custom_diff_style(
    *,
    node,
    node_class,
    current_only: list[str],
    reference_only: list[str],
    edit: list[str],
):
    """Custom visualization style for the diff of 2 dataflows"""
    if node.name in current_only:
        style = ({"fillcolor": "greenyellow"}, node_class, "Current only")

    elif node.name in reference_only:
        style = ({"fillcolor": "tomato1"}, node_class, "Reference only")

    elif node.name in edit:
        style = ({"fillcolor": "yellow2"}, node_class, "Edited")

    else:
        style = ({}, node_class, None)

    return style


def visualize_diff(
    current_dr: driver.Driver,
    reference_dr: driver.Driver,
    current_only: list[str],
    reference_only: list[str],
    edit: list[str],
):
    """Visualize the diff of 2 dataflows.

    Uses the union of sets of nodes from driver 1 and driver 2.
    """
    import functools

    from hamilton import graph

    all_nodes = set(reference_dr.graph.get_nodes()).union(set(current_dr.graph.get_nodes()))

    diff_style = functools.partial(
        _custom_diff_style,
        current_only=current_only,
        reference_only=reference_only,
        edit=edit,
    )

    return graph.create_graphviz_graph(
        nodes=all_nodes,
        comment="Diff viz",
        graphviz_kwargs=dict(),
        custom_style_function=diff_style,
        node_modifiers=dict(),
        strictly_display_only_nodes_passed_in=True,
    )


# TODO refactor ContextLoader to a class
# TODO support loading from pyproject.toml
def load_context(file_path: Path) -> dict:
    if not file_path.exists():
        raise FileNotFoundError(f"`{file_path}` doesn't exist.")

    extension = file_path.suffix
    if extension == ".json":
        context = _read_json_context(file_path)
    elif extension == ".py":
        context = _read_py_context(file_path)
    else:
        raise ValueError(f"Received extension `{extension}` is unsupported.")

    context = _validate_context(context)
    return context


def _validate_context(context: dict) -> dict:
    if context[CONFIG_HEADER] is None:
        context[CONFIG_HEADER] = {}

    if context[FINAL_VARS_HEADER] is None:
        context[FINAL_VARS_HEADER] = []

    if context[INPUTS_HEADER] is None:
        context[INPUTS_HEADER] = {}

    if context[OVERRIDES_HEADER] is None:
        context[OVERRIDES_HEADER] = {}

    return context


def _read_json_context(file_path: Path) -> dict:
    """"""
    import json

    data = json.load(file_path.open())

    context = {}
    for k in [
        CONFIG_HEADER,
        FINAL_VARS_HEADER,
        INPUTS_HEADER,
        OVERRIDES_HEADER,
    ]:
        context[k] = data.get(k, None)

    return context


def _read_py_context(file_path: Path) -> dict:
    import importlib

    spec = importlib.util.spec_from_file_location("cli_config", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    context = {}
    for k in [
        CONFIG_HEADER,
        FINAL_VARS_HEADER,
        INPUTS_HEADER,
        OVERRIDES_HEADER,
    ]:
        context[k] = getattr(module, k, None)

    return context


def _import_module_for_testgen(module_path: Path):
    """Import a Hamilton module from source for test-stub generation.

    Temporarily puts the module's directory on sys.path so sibling imports
    resolve, and raises a clear error when the module cannot be imported.
    """
    import sys

    from hamilton import ad_hoc_utils

    module_dir = str(module_path.resolve().parent)
    added = module_dir not in sys.path
    if added:
        sys.path.insert(0, module_dir)
    try:
        return ad_hoc_utils.module_from_source(module_path.read_text())
    except ImportError as e:
        raise ImportError(
            f"Could not import {module_path.name} to generate test stubs: {e}. "
            "Run the command from an environment where the module's imports resolve."
        ) from e
    finally:
        if added:
            sys.path.remove(module_dir)


def _existing_test_names(test_file_path: Path) -> set:
    """Return the names of test functions already defined in the given file."""
    import ast

    if not test_file_path.exists():
        return set()
    try:
        tree = ast.parse(test_file_path.read_text())
    except (SyntaxError, ValueError):
        return set()
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    }


def _annotation_name(annotation) -> str:
    """Best-effort readable name for a parameter annotation."""
    import inspect

    if annotation is inspect.Parameter.empty:
        return ""
    if hasattr(annotation, "__name__"):
        module = getattr(annotation, "__module__", "") or ""
        if module.startswith("pandas"):
            return f"pd.{annotation.__name__}"
        return annotation.__name__
    return str(annotation).replace("typing.", "")


def render_test_stub(func_name: str, func, module_name: str) -> str:
    """Render a pytest-style unit test stub for a single Hamilton function."""
    import inspect

    signature = inspect.signature(func)
    return_annotation = _annotation_name(signature.return_annotation)
    returns_pandas = "Series" in return_annotation or "DataFrame" in return_annotation

    uses_pandas = returns_pandas
    setup_lines = []
    call_args = []
    for param in signature.parameters.values():
        annotation = _annotation_name(param.annotation)
        if "Series" in annotation or "DataFrame" in annotation:
            uses_pandas = True
            default = "pd.Series([])" if "Series" in annotation else "pd.DataFrame({})"
            setup_lines.append(f"    {param.name}: {annotation} = {default}  # TODO: fill in")
        elif annotation:
            setup_lines.append(f"    {param.name}: {annotation} = None  # TODO: fill in")
        else:
            setup_lines.append(f"    {param.name} = None  # TODO: fill in")
        call_args.append(param.name)

    call_expr = f"{module_name}.{func_name}({', '.join(call_args)})"
    if returns_pandas:
        expected_placeholder = "pd.Series([])" if "Series" in return_annotation else "pd.DataFrame({})"
        check_lines = [
            f"    expected = {expected_placeholder}  # TODO: fill in",
            f"    actual = {call_expr}",
            "    # comparing pandas objects: use the pandas testing module",
            "    pd.testing.assert_series_equal(actual, expected)"
            if "Series" in return_annotation
            else "    pd.testing.assert_frame_equal(actual, expected)",
        ]
    else:
        check_lines = [
            "    expected = None  # TODO: fill in",
            f"    actual = {call_expr}",
            "    assert actual == expected",
        ]

    body = "\n".join(setup_lines + check_lines)
    return f"def test_{func_name}():\n{body}\n"


def create_test_stubs(
    module_path: Path, output_file: Path | None = None
) -> tuple[Path, list, list]:
    """Generate pytest-style unit test stubs for the Hamilton functions in a module.

    Appends to the output file when it exists and skips functions that already
    have a test defined. Returns (output_path, created_test_names, skipped_test_names).
    """
    from hamilton import ad_hoc_utils, graph_utils

    module_name = module_path.stem
    if output_file is None:
        output_file = module_path.parent / f"test_{module_name}.py"

    mod = _import_module_for_testgen(module_path)
    already_present = _existing_test_names(output_file)

    created = []
    skipped = []
    stubs = []
    for func_name, func_obj in graph_utils.find_functions(mod):
        test_name = f"test_{func_name}"
        if test_name in already_present:
            skipped.append(test_name)
            continue
        stubs.append(render_test_stub(func_name, func_obj, module_name))
        created.append(test_name)

    if stubs:
        uses_pandas = any("pd." in stub for stub in stubs)
        if output_file.exists():
            existing = output_file.read_text()
            separator = "" if existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
            output_file.write_text(existing + separator + "\n\n".join(stubs) + "\n")
        else:
            header_lines = []
            if uses_pandas:
                header_lines.append("import pandas as pd")
            header_lines.append(f"import {module_name}")
            header = "\n".join(header_lines) + "\n\n\n"
            output_file.write_text(header + "\n\n".join(stubs) + "\n")

    return output_file, created, skipped
