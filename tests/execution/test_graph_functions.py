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

from typing import Callable, Dict, List, Union

import pytest

from hamilton import node
from hamilton.execution.graph_functions import (
    create_input_string,
    nodes_between,
    topologically_sort_nodes,
)


def _create_dummy_dag(
    adjacency_map: Dict[str, List[str]], dict_output: bool = False
) -> Union[List[node.Node], Dict[str, node.Node]]:
    name_map = {}
    for name, dependencies in adjacency_map.items():
        input_types = {dep: object for dep in dependencies}
        node_ = node.Node(
            name=name,
            typ=object,
            callabl=lambda **kwargs: object(),
            input_types=input_types,
        )
        name_map[name] = node_
    nodes = []
    for name, dependencies in adjacency_map.items():
        node_ = name_map[name]
        for dependency in dependencies:
            dep = name_map[dependency]
            dep.depended_on_by.append(node_)
            node_.dependencies.append(name_map[dependency])
        nodes.append(node_)
    if dict_output:
        return {node_.name: node_ for node_ in nodes}
    return nodes


def _assert_topologically_sorted(nodes, sorted_nodes):
    for node_ in nodes:
        for dep in node_.dependencies:
            assert sorted_nodes.index(dep.name) < sorted_nodes.index(node_.name)


@pytest.mark.parametrize(
    "dag_input, expected_sorted_nodes",
    [
        ({"a": [], "b": ["a"], "c": ["a"], "d": ["b", "c"], "e": ["d"]}, ["a", "b", "c", "d", "e"]),
        ({}, []),
        ({"a": []}, ["a"]),
        (
            {
                "a": ["b", "c"],
                "b": ["d", "e"],
                "c": ["d", "e"],
                "d": ["f"],
                "e": ["f", "g"],
                "f": ["h"],
                "g": ["h", "i"],
                "h": ["j", "k"],
                "i": ["k", "l"],
                "j": ["m"],
                "k": ["m", "n"],
                "l": ["n"],
                "m": ["o"],
                "n": ["o", "p"],
                "o": ["q"],
                "p": ["q"],
                "q": [],
            },
            ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q"],
        ),
    ],
    ids=[
        "Simple DAG",
        "Empty DAG",
        "Single Node DAG",
        "Large DAG",
    ],
)
def test_topologically_sort_nodes(dag_input, expected_sorted_nodes):
    nodes = _create_dummy_dag(dag_input)
    sorted_nodes = [item.name for item in topologically_sort_nodes(nodes)]
    _assert_topologically_sorted(nodes, sorted_nodes)


def _is(name: str) -> Callable[[node.Node], bool]:
    def _inner(n: node.Node) -> bool:
        return n.name == name

    return _inner


@pytest.mark.parametrize(
    "dag_repr, expected_nodes_in_between, start_node, end_node",
    [
        (
            {"a": [], "b": ["a"], "c": ["b"]},
            {"b"},
            "a",
            "c",
        ),
        (
            {"a": [], "b": ["a"], "c": ["b"], "d": ["c"], "e": ["d"]},
            {"b", "c", "d"},
            "a",
            "e",
        ),
        (
            {
                "a": ["b", "c"],
                "b": ["d"],
                "c": ["d"],
                "d": ["e"],
                "e": ["f"],
                "f": ["g"],
                "g": ["h"],
                "h": ["i", "j"],
                "i": ["k"],
                "j": ["k"],
                "k": ["l"],
                "l": ["m", "n"],
                "m": ["o"],
                "n": ["o"],
                "o": ["p"],
                "p": ["q"],
                "q": [],
            },
            {"e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p"},
            "q",
            "d",
        ),
        ({"a": [], "b": [], "c": ["a", "b"], "d": "c"}, {"c"}, "a", "d"),
        # https://github.com/apache/hamilton/issues/948
        (
            {
                "random_int": [],
                "numbers": ["random_int"],
                "add1": ["numbers", "random_int"],
                "add2": ["add1", "random_int"],
                "collect_numbers": ["add2"],
                "final_result": ["collect_numbers"],
            },
            {"add1", "add2"},
            "numbers",
            "collect_numbers",
        ),
    ],
    ids=["simple_base", "longer_chain", "complex_dag", "subdag_with_external_dep", "issue_948"],
)
def test_find_nodes_between(dag_repr, expected_nodes_in_between, start_node, end_node):
    nodes = _create_dummy_dag(dag_repr, dict_output=True)
    found_node, in_between = nodes_between(nodes[end_node], _is(start_node))
    assert found_node.name == start_node
    assert set(in_between) == {nodes[item] for item in expected_nodes_in_between}


def test_create_input_string_with_short_values():
    """Tests that create_input_string works correctly with short values"""
    kwargs = {"arg1": 1, "arg2": "short string", "arg3": 3.14}
    result = create_input_string(kwargs)
    assert result == "{'arg1': 1, 'arg2': 'short string', 'arg3': 3.14}"


def test_create_input_string_with_long_values():
    """Tests that create_input_string truncates long values"""
    kwargs = {"arg1": "a" * 51, "arg2": "b" * 52, "arg3": "c" * 53}
    result = create_input_string(kwargs)
    assert result == (
        "{'arg1': \"'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa...\",\n"
        " 'arg2': \"'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb...\",\n"
        " 'arg3': \"'ccccccccccccccccccccccccccccccccccccccccccccccccc...\"}"
    )


def test_create_input_string_with_empty_dict():
    """Tests that create_input_string works correctly with an empty dictionary"""
    kwargs = {}
    result = create_input_string(kwargs)
    assert result == "{}"


def test_create_input_string_with_large_number_of_args():
    """Tests that create_input_string truncates the output if there are too many arguments"""
    kwargs = {f"arg{i}": i for i in range(1000)}
    result = create_input_string(kwargs)
    assert result.startswith("{")
    assert result.endswith("...")
    assert len(result) == 1003


def test_create_input_string_with_dataframes():
    """Tests that create_input_string works correctly with pandas dataframes"""
    import pandas as pd

    kwargs = {
        "arg1": pd.DataFrame({"a": [1, 2, 3] * 10, "b": [4, 5, 6] * 10}),
        "arg2": "short string",
        "arg3": 3.14,
    }
    result = create_input_string(kwargs)
    assert result == (
        "{'arg1': '    a  b\\n0   1  4\\n1   2  5\\n2   3  6\\n3   1  4\\n4   2...',\n"
        " 'arg2': 'short string',\n"
        " 'arg3': 3.14}"
    )


def test_create_input_string_with_custom_object():
    """Tests that create_input_string works correctly with custom objects"""

    class CustomObject:
        def __init__(self, a, b):
            self.a = a
            self.b = b

    kwargs = {"arg1": CustomObject(1, 2), "arg2": "short string", "arg3": 3.14}
    result = create_input_string(kwargs)
    assert result == (
        "{'arg1': '<tests.execution.test_graph_functions.test_create_...',\n"
        " 'arg2': 'short string',\n"
        " 'arg3': 3.14}"
    )
