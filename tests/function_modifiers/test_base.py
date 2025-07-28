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

from typing import Collection, Dict, List

import pytest as pytest

from hamilton import node, settings
from hamilton.function_modifiers import InvalidDecoratorException, base
from hamilton.function_modifiers.base import (
    MissingConfigParametersException,
    NodeTransformer,
    TargetType,
)
from hamilton.node import Node

power_mode_k = settings.ENABLE_POWER_USER_MODE


@pytest.mark.parametrize(
    "config,config_required,config_optional_with_defaults,expected",
    [
        ({"foo": 1}, ["foo"], None, {"foo": 1, power_mode_k: False}),
        ({"foo": 1}, ["foo"], {}, {"foo": 1, power_mode_k: False}),
        ({"foo": 1, "bar": 2}, ["foo"], {}, {"foo": 1, power_mode_k: False}),
        ({"foo": 1, "bar": 2}, ["foo"], {"bar": 3}, {"foo": 1, "bar": 2, power_mode_k: False}),
        ({"foo": 1}, [], {"bar": 3}, {"bar": 3, power_mode_k: False}),
        ({"foo": 1, power_mode_k: True}, ["foo"], {}, {"foo": 1, power_mode_k: True}),
        ({"foo": 1, "bar": 2, power_mode_k: True}, ["foo"], {}, {"foo": 1, power_mode_k: True}),
        (
            {"foo": 1, "bar": 2, power_mode_k: True},
            ["foo"],
            {"bar": 3},
            {"foo": 1, "bar": 2, power_mode_k: True},
        ),
        ({"foo": 1, power_mode_k: True}, [], {"bar": 3}, {"bar": 3, power_mode_k: True}),
    ],
    ids=[
        "all_present_no_optional",
        "all_present",
        "all_present_extra",
        "no_apply_default",
        "yes_apply_default",
        "all_present_with_power_user_mode",
        "all_present_extra_with_power_user_mode",
        "no_apply_default_with_power_user_mode",
        "yes_apply_default_with_power_user_mode",
    ],
)
def test_merge_config_happy(config, config_required, config_optional_with_defaults, expected):
    assert (
        base.resolve_config("test", config, config_required, config_optional_with_defaults)
        == expected
    )


@pytest.mark.parametrize(
    "config,config_required,config_optional_with_defaults",
    [
        ({"foo": 1}, ["bar"], {}),
        ({"bar": 2}, ["foo"], {"baz": 3}),
    ],
    ids=["wrong_one", "wrong_optional"],
)
def test_merge_config_sad(config, config_required, config_optional_with_defaults):
    with pytest.raises(MissingConfigParametersException):
        base.resolve_config("test", config, config_required, config_optional_with_defaults)


def _create_node_set(names_to_deps: Dict[str, List[str]]) -> List[Node]:
    nodes = []
    for name, deps in names_to_deps.items():
        nodes.append(
            node.Node(
                name=name,
                typ=int,
                doc_string="",
                callabl=lambda: 1,
                input_types={dep: (int, node.DependencyType.REQUIRED) for dep in deps},
            )
        )
    return nodes


@pytest.mark.parametrize(
    "target,nodes,expected",
    [
        # Testing None -- E.G. final nodes
        (None, {}, []),
        (None, _create_node_set({"a": []}), ["a"]),
        (None, _create_node_set({"a": [], "b": ["a"], "c": ["b"]}), ["c"]),
        (None, _create_node_set({"a": ["b"], "b": ["c"], "c": []}), ["a"]),
        (None, _create_node_set({"d": ["b"], "a": ["b"], "b": ["c"], "c": []}), ["a", "d"]),
        # Testing ellipsis -- E.G. all nodes
        (..., {}, []),
        (..., _create_node_set({"a": []}), ["a"]),
        (..., _create_node_set({"a": [], "b": ["a"], "c": ["b"]}), ["c", "b", "a"]),
        (..., _create_node_set({"a": ["b"], "b": ["c"], "c": []}), ["a", "b", "c"]),
        (
            ...,
            _create_node_set({"d": ["b"], "a": ["b"], "b": ["c"], "c": []}),
            ["a", "b", "c", "d"],
        ),
        # Testing string -- E.G. single node
        ("a", _create_node_set({"a": []}), ["a"]),
        ("a", _create_node_set({"a": [], "b": ["a"], "c": ["b"]}), ["a"]),
        ("a", _create_node_set({"a": ["b"], "b": ["c"], "c": []}), ["a"]),
        ("a", _create_node_set({"d": ["b"], "a": ["b"], "b": ["c"], "c": []}), ["a"]),
        ("b", _create_node_set({"a": [], "b": ["a"], "c": ["b"]}), ["b"]),
        ("b", _create_node_set({"a": ["b"], "b": ["c"], "c": []}), ["b"]),
        ("b", _create_node_set({"d": ["b"], "a": ["b"], "b": ["c"], "c": []}), ["b"]),
        # Testing collection of string -- E.G. a list of node
        (["a"], _create_node_set({"a": []}), ["a"]),
        (["a"], _create_node_set({"a": [], "b": ["a"], "c": ["b"]}), ["a"]),
        (["a"], _create_node_set({"a": ["b"], "b": ["c"], "c": []}), ["a"]),
        (["a", "b"], _create_node_set({"d": ["b"], "a": ["b"], "b": ["c"], "c": []}), ["a", "b"]),
        (["b", "c"], _create_node_set({"a": [], "b": ["a"], "c": ["b"]}), ["b", "c"]),
        (["b", "c", "a"], _create_node_set({"a": ["b"], "b": ["c"], "c": []}), ["b", "c", "a"]),
        (
            ["a", "b", "c", "d"],
            _create_node_set({"d": ["b"], "a": ["b"], "b": ["c"], "c": []}),
            ["a", "b", "c", "d"],
        ),
    ],
)
def test_select_nodes_happy(
    target: TargetType, nodes: Collection[node.Node], expected: Collection[str]
):
    selected_nodes = [n.name for n in NodeTransformer.select_nodes(target, nodes)]
    assert sorted(selected_nodes) == sorted(expected)


@pytest.mark.parametrize(
    "target,nodes",
    [
        ("d", _create_node_set({"a": []})),
        (["d", "a"], _create_node_set({"a": []})),
        (["a", "b"], _create_node_set({"c": []})),
        (["d", "e"], _create_node_set({"d": ["e"]})),
    ],
)
def test_select_nodes_sad(target: TargetType, nodes: Collection[node.Node]):
    with pytest.raises(InvalidDecoratorException):
        NodeTransformer.select_nodes(target, nodes)


def test_add_fn_metadata():
    nodes_og = _create_node_set({"d": ["e"]})
    nodes = base._add_original_function_to_nodes(test_add_fn_metadata, nodes_og)
    nodes_with_fn_pointer = [
        n.originating_functions for n in nodes if n.originating_functions is not None
    ]
    assert len(nodes_with_fn_pointer) == len(nodes)
    assert all([n.originating_functions == (test_add_fn_metadata,) for n in nodes])
