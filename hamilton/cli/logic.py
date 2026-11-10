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

import ast
import builtins
import dataclasses
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


@dataclasses.dataclass(frozen=True)
class DiscoveredParameter:
    """A parameter of a discovered function, as written in the source file."""

    name: str
    kind: str  # one of POSITIONAL_KINDS / "var_positional" / "keyword_only" / "var_keyword"
    annotation: str  # source text, or "" when the parameter is not annotated
    annotation_roots: tuple[str, ...]  # names the annotation needs to evaluate, or ()
    default: str  # source text, or "" when the parameter has no default
    literal_default: bool  # True when the default can be written into the stub as-is


@dataclasses.dataclass(frozen=True)
class DiscoveredFunction:
    """A module-level function of the target module, read from its source only."""

    name: str
    parameters: tuple[DiscoveredParameter, ...]
    return_annotation: str  # source text, or ""


POSITIONAL_KINDS = ("positional_only", "positional_or_keyword")
LITERAL_TYPES = (ast.Constant, ast.List, ast.Tuple, ast.Set, ast.Dict, ast.UnaryOp)


def _discover_functions(module_path: Path) -> list[DiscoveredFunction]:
    """Read the module's functions and signatures from its source, without importing it.

    Importing the module would run its top-level code (arbitrary side effects) and would
    also fail for modules that use package-relative imports or that are not importable in
    this environment. Parsing covers the same functions that ``graph_utils.find_functions``
    selects: module-level definitions whose name does not start with an underscore. Async
    functions are skipped, because a generated synchronous test cannot await them.
    """
    source = module_path.read_text()
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError) as e:
        raise ValueError(f"Could not parse {module_path}: {e}") from e

    discovered = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name.startswith("_"):
            continue
        discovered.append(
            DiscoveredFunction(
                name=node.name,
                parameters=_discovered_parameters(node.args),
                return_annotation=_annotation_source(node.returns),
            )
        )
    return discovered


def _discovered_parameters(args) -> tuple[DiscoveredParameter, ...]:
    """Flatten ast.arguments into parameters, keeping each parameter's kind and defaults."""
    positional = [(a, "positional_only") for a in args.posonlyargs]
    positional += [(a, "positional_or_keyword") for a in args.args]
    defaults = list(args.defaults)
    # `defaults` aligns with the tail of posonlyargs + args
    positional_args = [arg for arg, _ in positional]
    default_of = {}
    for arg, default in zip(
        positional_args[len(positional_args) - len(defaults) :], defaults, strict=True
    ):
        default_of[arg.arg] = default
    for arg, default in zip(args.kwonlyargs, args.kw_defaults, strict=True):
        default_of[arg.arg] = default

    def build(arg, kind) -> DiscoveredParameter:
        default = default_of.get(arg.arg)
        return DiscoveredParameter(
            name=arg.arg,
            kind=kind,
            annotation=_annotation_source(arg.annotation),
            annotation_roots=_annotation_roots(arg.annotation),
            default=_annotation_source(default),
            literal_default=_is_literal(default),
        )

    parameters = [build(arg, kind) for arg, kind in positional]
    if args.vararg is not None:
        parameters.append(build(args.vararg, "var_positional"))
    parameters += [build(arg, "keyword_only") for arg in args.kwonlyargs]
    if args.kwarg is not None:
        parameters.append(build(args.kwarg, "var_keyword"))
    return tuple(parameters)


def _annotation_source(node) -> str:
    """Source text of an annotation or default; "" when absent."""
    if node is None:
        return ""
    return ast.unparse(node)


def _annotation_roots(node) -> tuple[str, ...]:
    """Names an annotation needs to evaluate, e.g. ("pd",) for ``pd.Series``."""
    if node is None:
        return ()
    roots = []
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id not in roots:
            roots.append(child.id)
    return tuple(roots)


def _is_literal(node) -> bool:
    """True when the default can be written into a stub without importing anything."""
    if node is None:
        return False
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, ast.UnaryOp):
        return isinstance(node.op, (ast.UAdd, ast.USub)) and _is_literal(node.operand)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return all(_is_literal(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        return all(
            _is_literal(k) and _is_literal(v) for k, v in zip(node.keys, node.values, strict=True)
        )
    return False


def _module_reference(module_path: Path) -> tuple[str, str]:
    """Return (import statement, reference) for the target module.

    A module inside a regular package (a directory with an ``__init__.py``) is imported by
    its dotted path (``pkg.mod``) so that its own relative imports resolve; a standalone
    module is imported by name. Namespace packages are not detected.
    """
    names = [module_path.stem]
    parent = module_path.resolve().parent
    while (parent / "__init__.py").exists():
        names.insert(0, parent.name)
        parent = parent.parent
    dotted = ".".join(names)
    return f"import {dotted}", dotted


def _existing_test_names(test_file_path: Path) -> set:
    """Return the names of test functions already defined in the given file."""
    if not test_file_path.exists():
        return set()
    try:
        tree = ast.parse(test_file_path.read_text())
    except (SyntaxError, ValueError):
        return set()
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }


def _imports_for_stubs(stubs: list[str], module_import: str) -> list[str]:
    """Imports a file needs to run the given stubs."""
    imports = []
    if any("pd." in stub for stub in stubs):
        imports.append("import pandas as pd")
    imports.append(module_import)
    return imports


def _bound_names(text: str) -> set:
    """Names bound by the top-level imports of a test file."""
    tree = ast.parse(text)
    bound = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound.add(alias.asname or alias.name.split(".")[0])
    return bound


def _imports_to_add(text: str, module_import: str, module_ref: str, stubs: list[str]) -> list[str]:
    """Which of the imports the new stubs need are missing from the file."""
    bound = _bound_names(text)
    missing = []
    if any("pd." in stub for stub in stubs) and "pd" not in bound:
        missing.append("import pandas as pd")
    # the stubs call `<root>.<...>.function(...)`, so the root name has to be bound by an
    # `import <dotted>` statement (binding `pkg` and importing `pkg.mod` in one go)
    root = module_ref.split(".")[0]
    dotted_imported = any(
        isinstance(node, ast.Import)
        and any(alias.name == module_ref and alias.asname is None for alias in node.names)
        for node in ast.walk(ast.parse(text))
    )
    if root not in bound or not dotted_imported:
        missing.append(module_import)
    return missing


def _import_insertion_index(text: str) -> int:
    """Line index at which missing imports can be inserted (0-based, in line units)."""
    lines = text.splitlines(keepends=True)
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return 0

    top_level_imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    if top_level_imports:
        return max(node.end_lineno for node in top_level_imports)

    index = 0
    first = tree.body[0] if tree.body else None
    if first is not None and isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
        if isinstance(first.value.value, str):
            index = first.end_lineno or 0
    while index < len(lines) and (lines[index].strip().startswith("#") or not lines[index].strip()):
        index += 1
    return index


def _ensure_imports(text: str, module_import: str, module_ref: str, stubs: list[str]) -> str:
    """Add the imports the new stubs need to an existing test file.

    Raises ``ValueError`` when the existing file is not valid Python: the file is left
    untouched rather than appended to.
    """
    try:
        missing = _imports_to_add(text, module_import, module_ref, stubs)
    except (SyntaxError, ValueError) as e:
        raise ValueError(
            f"Refusing to append to the existing test file, it is not valid Python: {e}"
        ) from e
    if not missing:
        return text

    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines(keepends=True)
    index = _import_insertion_index(text)
    block = [line + newline for line in missing]
    if index < len(lines) and lines[index].strip():
        block.append(newline)
    new_lines = lines[:index] + block + lines[index:]
    return "".join(new_lines)


def _placeholder(param: DiscoveredParameter, resolvable: set) -> tuple[str, str]:
    """The value and comment a stub assigns to a parameter."""
    annotation = param.annotation if set(param.annotation_roots) <= resolvable else ""
    is_pandas = "Series" in annotation or "DataFrame" in annotation
    notes = []
    if param.default and param.literal_default:
        value = param.default
    elif is_pandas:
        value = "pd.Series([])" if "Series" in annotation else "pd.DataFrame({})"
    elif param.kind == "var_positional":
        value = "()"
    elif param.kind == "var_keyword":
        value = "{}"
    else:
        value = "None"
    if param.default and not param.literal_default:
        notes.append(f"default is {param.default}")
    if param.annotation and not annotation:
        notes.append(f"declared as {param.annotation}")
    comment = "# TODO: fill in" + (f" ({'; '.join(notes)})" if notes else "")
    return value, comment


def render_test_stub(func: DiscoveredFunction, module_ref: str) -> str:
    """Render a pytest-style unit test stub for a single Hamilton function.

    Annotations and defaults are written into the stub only when the generated file can
    evaluate them on its own (builtins, ``pd`` and the target module); anything else
    becomes a placeholder with the original written in the TODO comment.
    """
    resolvable = {"pd"} | {module_ref.split(".")[0]} | set(dir(builtins))
    return_annotation = func.return_annotation
    resolvable_return = set(_annotation_roots_from_text(return_annotation)) <= resolvable
    if not resolvable_return:
        return_annotation = ""
    returns_pandas = "Series" in return_annotation or "DataFrame" in return_annotation

    setup_lines = []
    call_args = []
    for param in func.parameters:
        value, comment = _placeholder(param, resolvable)
        annotation = param.annotation if set(param.annotation_roots) <= resolvable else ""
        if param.kind in ("var_positional", "var_keyword"):
            # *args / **kwargs annotations describe the collected values, not the tuple/dict
            setup_lines.append(f"    {param.name} = {value}  {comment}")
        elif annotation:
            setup_lines.append(f"    {param.name}: {annotation} = {value}  {comment}")
        else:
            setup_lines.append(f"    {param.name} = {value}  {comment}")

        if param.kind in POSITIONAL_KINDS:
            call_args.append(param.name)
        elif param.kind == "var_positional":
            call_args.append(f"*{param.name}")
        elif param.kind == "keyword_only":
            call_args.append(f"{param.name}={param.name}")
        else:
            call_args.append(f"**{param.name}")

    call_expr = f"{module_ref}.{func.name}({', '.join(call_args)})"
    if returns_pandas:
        expected_placeholder = (
            "pd.Series([])" if "Series" in return_annotation else "pd.DataFrame({})"
        )
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
    return f"def test_{func.name}():\n{body}\n"


def _annotation_roots_from_text(annotation: str) -> tuple[str, ...]:
    """Names an annotation from source text needs to evaluate."""
    if not annotation:
        return ()
    try:
        node = ast.parse(annotation, mode="eval")
    except (SyntaxError, ValueError):
        return ("",)
    return _annotation_roots(node)


def create_test_stubs(
    module_path: Path, output_file: Path | None = None
) -> tuple[Path, list, list]:
    """Generate pytest-style unit test stubs for the Hamilton functions in a module.

    The target module is parsed, never imported, so generating stubs cannot run the
    module's top-level code or fail on imports that only resolve inside its package. The
    generated test file does import the module when the tests run, so any top-level code
    runs then.

    Appends to the output file when it exists (adding any import the new stubs need) and
    skips functions that already have a test defined there. A file that is not valid Python
    is left untouched. Returns (output_path, created, skipped).
    """
    module_import, module_ref = _module_reference(module_path)
    if output_file is None:
        output_file = module_path.parent / f"test_{module_path.stem}.py"

    existing = None
    if output_file.exists():
        existing = output_file.open("r", newline="").read()

    discovered = _discover_functions(module_path)
    already_present = _existing_test_names(output_file)

    created = []
    skipped = []
    stubs = []
    for func in discovered:
        test_name = f"test_{func.name}"
        if test_name in already_present:
            skipped.append(test_name)
            continue
        stubs.append(render_test_stub(func, module_ref))
        created.append(test_name)

    if stubs:
        new_content = "\n\n".join(stubs) + "\n"
        if existing is not None:
            existing = _ensure_imports(existing, module_import, module_ref, stubs)
            newline = "\r\n" if "\r\n" in existing else "\n"
            if "\n" != newline:
                new_content = new_content.replace("\n", newline)
            separator = "" if existing.endswith(newline + newline) else newline
            output_file.write_text(existing + separator + new_content)
        else:
            header = "\n".join(_imports_for_stubs(stubs, module_import)) + "\n\n\n"
            output_file.write_text(header + new_content)

    return output_file, created, skipped
