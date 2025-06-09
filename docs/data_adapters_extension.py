import dataclasses
import importlib
import inspect
import os
from typing import List, Optional, Tuple, Type

import git
from docutils import nodes
from docutils.parsers.rst import Directive

import hamilton.io.data_adapters
from hamilton import registry

"""A module to crawl available data adapters and generate documentation for them.
Note these currently link out to the source code on GitHub, but they should
be linking to the documentation instead, which hasn't been generated yet.
"""

# These have fallbacks for local dev
GIT_URL = os.environ.get("READTHEDOCS_GIT_CLONE_URL", "https://github.com/apache/hamilton")
GIT_ID = os.environ.get("READTHEDOCS_GIT_IDENTIFIER", "main")

# All the modules that register data adapters
# When you register a new one, add it here

# Keep these two around so we
importlib.import_module("hamilton.function_modifiers.base")
importlib.import_module("hamilton.io")


def get_git_root(path: str) -> str:
    """Yields the git room of a repo, given an absolute path to
    a file within the repo.

    :param path: Path to a file within a git repo
    :return:  The root of the git repo
    """
    git_repo = git.Repo(path, search_parent_directories=True)
    git_root = git_repo.git.rev_parse("--show-toplevel")
    return git_root


@dataclasses.dataclass
class Param:
    name: str
    type: str
    default: Optional[str] = None


def get_default(param: dataclasses.Field) -> Optional[str]:
    """Gets the deafult of a dataclass field, if it has one.

    :param param:  The dataclass field
    :return: The str representation of the default.
    """
    if param.default is dataclasses.MISSING:
        return None
    return str(param.default)


def get_lines_for_class(class_: Type[Type]) -> Tuple[int, int]:
    """Gets the set of lines in which a class is implemented

    :param class_: The class to get the lines for
    :return: A tuple of the start and end lines
    """
    lines = inspect.getsourcelines(class_)
    start_line = lines[1]
    end_line = lines[1] + len(lines[0])
    return start_line, end_line


def get_class_repr(class_: Type) -> str:
    """Gets a representation of a class that can be used in documentation.

    :param class_: Python class to get the representation for
    :return: Str representation
    """

    try:
        return class_.__qualname__
    except AttributeError:
        # This happens when we have generics or other oddities
        return str(class_)


@dataclasses.dataclass
class AdapterInfo:
    key: str
    class_name: str
    class_path: str
    load_params: List[Param]
    save_params: List[Param]
    applicable_types: List[str]
    file_: str
    line_nos: Tuple[int, int]

    @staticmethod
    def from_loader(loader: Type[hamilton.io.data_adapters.DataLoader]) -> "AdapterInfo":
        """Utility constructor to create the AdapterInfo from a DataLoader class

        :param loader: DataLoader class
        :return: AdapterInfo derived from it
        """

        return AdapterInfo(
            key=loader.name(),
            class_name=loader.__name__,
            class_path=loader.__module__,
            load_params=(
                [
                    Param(name=p.name, type=get_class_repr(p.type), default=get_default(p))
                    for p in dataclasses.fields(loader)
                ]
                if issubclass(loader, hamilton.io.data_adapters.DataLoader)
                else None
            ),
            save_params=(
                [
                    Param(name=p.name, type=get_class_repr(p.type), default=get_default(p))
                    for p in dataclasses.fields(loader)
                ]
                if issubclass(loader, hamilton.io.data_adapters.DataSaver)
                else None
            ),
            applicable_types=[get_class_repr(t) for t in loader.applicable_types()],
            file_=inspect.getfile(loader),
            line_nos=get_lines_for_class(loader),
        )


def _collect_loaders(saver_or_loader: str) -> List[Type[hamilton.io.data_adapters.AdapterCommon]]:
    """Collects all loaders from the registry.

    :return:
    """
    out = []
    loaders = (
        list(registry.LOADER_REGISTRY.values())
        if saver_or_loader == "loader"
        else list(registry.SAVER_REGISTRY.values())
    )
    for classes in loaders:
        for cls in classes:
            if cls not in out:
                out.append(cls)
    return out


# Utility functions to render different components of the adapter in table cells


def render_key(key: str):
    return [nodes.Text(key, key)]


def render_class_name(class_name: str):
    return [nodes.literal(text=class_name)]


def render_class_path(class_path: str, file_: str, line_start: int, line_end: int):
    git_path = get_git_root(file_)
    file_relative_to_git_root = os.path.relpath(file_, git_path)
    href = f"{GIT_URL}/blob/{GIT_ID}/{file_relative_to_git_root}#L{line_start}-L{line_end}"
    # href = f"{GIT_URL}/blob/{GIT_ID}/{file_}#L{line_no}"
    return [nodes.raw("", f'<a href="{href}">{class_path}</a>', format="html")]


def render_adapter_params(load_params: Optional[List[Param]]):
    if load_params is None:
        return nodes.raw("", "<div/>", format="html")
    fieldlist = nodes.field_list()
    for i, load_param in enumerate(load_params):
        fieldname = nodes.Text(load_param.name)
        fieldbody = nodes.literal(
            text=load_param.type
            + ("=" + load_param.default if load_param.default is not None else "")
        )
        field = nodes.field("", fieldname, fieldbody)
        fieldlist += field
        if i < len(load_params) - 1:
            fieldlist += nodes.raw("", "<br/>", format="html")
    return fieldlist


def render_applicable_types(applicable_types: List[str]):
    fieldlist = nodes.field_list()
    for applicable_type in applicable_types:
        fieldlist += nodes.field("", nodes.literal(text=applicable_type), nodes.Text(""))
        fieldlist += nodes.raw("", "<br/>", format="html")
    return fieldlist


class DataAdapterTableDirective(Directive):
    """Custom directive to render a table of all data adapters. Takes in one argument
    that is either 'loader' or 'saver' to indicate which adapters to render."""

    has_content = True
    required_arguments = 1  # Number of required arguments

    def run(self):
        """Runs the directive. This does the following:
        1. Collects all loaders from the registry
        2. Creates a table with the following columns:
            - Key
            - Class name
            - Class path
            - Load params
            - Applicable types
        3. Returns the table
        :return: A list of nodes that Sphinx will render, consisting of the table node
        """
        saver_or_loader = self.arguments[0]
        if saver_or_loader not in ("loader", "saver"):
            raise ValueError(
                f"loader_or_saver must be one of 'loader' or 'saver', " f"got {saver_or_loader}"
            )
        table_data = [
            AdapterInfo.from_loader(loader) for loader in _collect_loaders(saver_or_loader)
        ]

        # Create the table and add columns
        table_node = nodes.table()
        tgroup = nodes.tgroup(cols=6)
        table_node += tgroup

        # Create columns
        key_spec = nodes.colspec(colwidth=1)
        # class_spec = nodes.colspec(colwidth=1)
        load_params_spec = nodes.colspec(colwidth=2)
        applicable_types_spec = nodes.colspec(colwidth=1)
        class_path_spec = nodes.colspec(colwidth=1)

        tgroup += [key_spec, load_params_spec, applicable_types_spec, class_path_spec]

        # Create the table body
        thead = nodes.thead()
        row = nodes.row()

        # Create entry nodes for each cell
        key_entry = nodes.entry()
        load_params_entry = nodes.entry()
        applicable_types_entry = nodes.entry()
        class_path_entry = nodes.entry()

        key_entry += nodes.paragraph(text="key")

        load_params_entry += nodes.paragraph(text=f"{saver_or_loader} params")
        applicable_types_entry += nodes.paragraph(text="types")
        class_path_entry += nodes.paragraph(text="module")

        row += [key_entry, load_params_entry, applicable_types_entry, class_path_entry]
        thead += row
        tgroup += thead
        tbody = nodes.tbody()
        tgroup += tbody

        # Populate table rows based on your table_data
        for row_data in table_data:
            row = nodes.row()

            # Create entry nodes for each cell
            key_entry = nodes.entry()
            load_params_entry = nodes.entry()
            applicable_types_entry = nodes.entry()
            class_path_entry = nodes.entry()

            # Create a paragraph node for each entry
            # import pdb
            # pdb.set_trace()
            # para1 = nodes.literal(text=row_data['column1_data'])
            # para2 = nodes.paragraph(text=row_data['column2_data'])

            # Add the paragraph nodes to the entry nodes
            key_entry += render_key(row_data.key)
            load_params_entry += render_adapter_params(
                row_data.load_params if saver_or_loader == "loader" else row_data.save_params
            )
            applicable_types_entry += render_applicable_types(row_data.applicable_types)
            class_path_entry += render_class_path(
                row_data.class_path, row_data.file_, *row_data.line_nos
            )

            # Add the entry nodes to the row
            row += [key_entry, load_params_entry, applicable_types_entry, class_path_entry]

            # Add the row to the table body
            tbody += row

        return [table_node]


def setup(app):
    """Required to register the extension"""
    app.add_directive("data_adapter_table", DataAdapterTableDirective)
