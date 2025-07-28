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

import inspect
import json
import sys
import textwrap

import pytest

from hamilton import driver, graph_types, node
from hamilton.node import Node, NodeType

from tests import nodes as test_nodes
from tests.resources.dynamic_parallelism import no_parallel


@pytest.fixture()
def func_a():
    """Default function implementation"""

    return textwrap.dedent(
        """
        def A(external_input: int) -> int:
            return external_input % 7
        """
    )


@pytest.fixture()
def func_a_body():
    """The function A() has modulo 5 instead of 7"""

    return textwrap.dedent(
        """
        def A(external_input: int) -> int:
            return external_input % 5
        """
    )


@pytest.fixture()
def func_a_docstring():
    """The function A() has a docstring"""

    return textwrap.dedent(
        """
        def A(external_input: int) -> int:
            '''This one has a docstring'''
            return external_input % 7
        """
    )


@pytest.fixture()
def func_a_multiline():
    """The function A() has a docstring"""

    return textwrap.dedent(
        """
        def A(external_input: int) -> int:
            '''This one has
            a multiline
            docstring
            '''
            return external_input % 7
        """
    )


@pytest.fixture()
def func_a_comment():
    """The function A() has a comment"""

    return textwrap.dedent(
        """
        def A(external_input: int) -> int:
            return external_input % 7  # a comment
        """
    )


def test_create_hamilton_node():
    def node_to_create(required_dep: int, optional_dep: int = 1) -> str:
        """Documentation"""
        return f"{required_dep}_{optional_dep}"

    n = node.Node.from_fn(
        node_to_create
    ).copy_with(  # The following simulate the graph's creation of a node
        tags={"tag_key": "tag_value"}, originating_functions=(node_to_create,)
    )
    hamilton_node = graph_types.HamiltonNode.from_node(n)
    assert hamilton_node.name == "node_to_create"
    assert hamilton_node.type == str
    assert hamilton_node.tags["tag_key"] == "tag_value"
    assert hamilton_node.originating_functions == (node_to_create,)
    assert hamilton_node.documentation == "Documentation"
    assert not hamilton_node.is_external_input
    assert hamilton_node.required_dependencies == {"required_dep"}
    assert hamilton_node.optional_dependencies == {"optional_dep"}
    assert hamilton_node.version == graph_types.hash_source_code(node_to_create, strip=True)

    assert hamilton_node.as_dict(include_optional_dependencies_default_values=True) == {
        "name": "node_to_create",
        "tags": {"tag_key": "tag_value"},
        "output_type": "str",
        "required_dependencies": ["required_dep"],
        "optional_dependencies": ["optional_dep"],
        "optional_dependencies_default_values": {"optional_dep": 1},
        "source": (
            "    def node_to_create(required_dep: int, optional_dep: int = 1) -> str:\n"
            '        """Documentation"""\n'
            '        return f"{required_dep}_{optional_dep}"\n'
        ),
        "documentation": "Documentation",
        "version": graph_types.hash_source_code(node_to_create, strip=True),
    }


def test_create_hamilton_config_node_version():
    """Config nodes now return the name as the version."""
    n = Node("foo", int, node_source=NodeType.EXTERNAL)
    hamilton_node = graph_types.HamiltonNode.from_node(n)
    # the above will have no specified versions
    assert hamilton_node.version == "foo"
    assert hamilton_node.as_dict()["version"] == "foo"


def test_create_hamilton_node_missing_version():
    """We contrive a case where originating_functions is None."""

    def foo(i: int) -> int:
        return i

    n = Node("foo", int, "", foo, node_source=NodeType.STANDARD)
    hamilton_node = graph_types.HamiltonNode.from_node(n)
    # the above will have no specified versions
    assert hamilton_node.version is None
    assert hamilton_node.as_dict()["version"] is None


def test_hamilton_graph_version_normal():
    dr = driver.Builder().with_modules(no_parallel).build()
    graph = graph_types.HamiltonGraph.from_graph(dr.graph)
    # assumption is for python 3
    if sys.version_info.minor == 8:
        hash_value = "0a375f3366590453dea8927d4c02c15dc090f8be42e9129d9a1139284eac920c"
    else:
        hash_value = "3b3487599ccc4fc56995989c6d32b58a90c0b91b8c16b3f453a2793f47436831"
    assert graph.version == hash_value


def test_hamilton_graph_version_with_none_originating_functions():
    dr = driver.Builder().with_modules(no_parallel).build()
    graph = graph_types.HamiltonGraph.from_graph(dr.graph)
    # if this gets flakey we should find a specific node to make None
    graph.nodes[-1].originating_functions = None
    # assumption is for python 3
    if sys.version_info.minor == 8:
        hash_value = "7d556424cd84b97a395d9b6219f502e8f818f17002ce88f47974266c0cce454a"
    else:
        hash_value = "781d89517c1744c40a7afcdc49ee8592fbb23955e28d87f1b584d08430a3e837"
    assert graph.version == hash_value


def test_hamilton_graph_getitem():
    dr = driver.Builder().with_modules(test_nodes).build()
    h_graph = graph_types.HamiltonGraph.from_graph(dr.graph)

    assert isinstance(h_graph["lowercased"], graph_types.HamiltonNode)
    assert h_graph["lowercased"].name == "lowercased"


def test_hamilton_graph_filter_nodes():
    dr = driver.Builder().with_modules(test_nodes).build()
    h_graph = graph_types.HamiltonGraph.from_graph(dr.graph)

    # could be a lambda but flake8 doesn't like it.
    def filter_cache_equal_str(n: graph_types.HamiltonNode) -> bool:
        return n.tags.get("cache") == "str"

    node_selection = h_graph.filter_nodes(filter=filter_cache_equal_str)
    node_names = [n.name for n in node_selection]

    assert len(node_selection) == 2
    assert "lowercased" in node_names
    assert "uppercased" in node_names


def test_json_serializable_dict():
    for name, obj in inspect.getmembers(test_nodes):
        if inspect.isfunction(obj) and not name.startswith("_"):
            n = node.Node.from_fn(
                obj
            ).copy_with(  # The following simulate the graph's creation of a node
                originating_functions=(obj,)
            )
            hamilton_node = graph_types.HamiltonNode.from_node(n)

            # Check that json.dumps works on all nodes
            json.dumps(hamilton_node.as_dict())


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires Python 3.9 or higher")
def test_remove_docstring(func_a: str, func_a_docstring: str):
    func_a_no_whitespace = func_a.strip()
    stripped = graph_types._remove_docs_and_comments(func_a_docstring)
    assert func_a_no_whitespace == stripped


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires Python 3.9 or higher")
def test_remove_multiline(func_a: str, func_a_multiline: str):
    func_a_no_whitespace = func_a.strip()
    stripped = graph_types._remove_docs_and_comments(func_a_multiline)
    assert func_a_no_whitespace == stripped


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires Python 3.9 or higher")
def test_remove_comment(func_a: str, func_a_comment: str):
    func_a_no_whitespace = func_a.strip()
    stripped = graph_types._remove_docs_and_comments(func_a_comment)
    assert func_a_no_whitespace == stripped


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires Python 3.9 or higher")
@pytest.mark.parametrize("strip", [True, False])
def test_different_hash_function_body(func_a: str, func_a_body: str, strip: bool):
    """Gives different hash for different function body"""
    func_a_hash = graph_types.hash_source_code(func_a, strip=strip)
    func_a_body_hash = graph_types.hash_source_code(func_a_body, strip=strip)
    assert func_a_hash != func_a_body_hash


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires Python 3.9 or higher")
@pytest.mark.parametrize("strip", [True, False])
def test_different_hash_docstring(func_a: str, func_a_docstring: str, strip: bool):
    """Same hash if strip docstring, else different hash"""
    func_a_hash = graph_types.hash_source_code(func_a, strip=strip)
    func_a_docstring_hash = graph_types.hash_source_code(func_a_docstring, strip=strip)
    assert (func_a_hash == func_a_docstring_hash) is (True if strip else False)


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires Python 3.9 or higher")
@pytest.mark.parametrize("strip", [True, False])
def test_different_hash_multiline_docstring(func_a: str, func_a_multiline: str, strip: bool):
    """Same hash if strip multiline docstring, else different hash"""
    func_a_hash = graph_types.hash_source_code(func_a, strip=strip)
    func_a_multiline_hash = graph_types.hash_source_code(func_a_multiline, strip=strip)
    assert (func_a_hash == func_a_multiline_hash) is (True if strip else False)


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires Python 3.9 or higher")
@pytest.mark.parametrize("strip", [True, False])
def test_different_hash_comment(func_a: str, func_a_comment: str, strip: bool):
    """Same hash if strip comment, else different hash"""
    func_a_hash = graph_types.hash_source_code(func_a, strip=strip)
    func_a_comment = graph_types.hash_source_code(func_a_comment, strip=strip)
    assert (func_a_hash == func_a_comment) is (True if strip else False)
