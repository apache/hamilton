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
import sys
from typing import Any, Literal, TypeVar

import numpy as np
import numpy.typing as npt
import pytest

from hamilton import node
from hamilton.node import DependencyType, Node, matches_query

from tests.resources import nodes_with_future_annotation


def test_node_from_fn_happy():
    def fn() -> int:
        return 1

    node = Node.from_fn(fn)
    assert node.name == "fn"
    assert node.callable() == 1
    assert node.input_types == {}
    assert node.type == int


def test_node_from_fn_sad_no_type_hint():
    def fn():
        return 1

    with pytest.raises(ValueError):
        Node.from_fn(fn)


def test_node_copy_with_retains_originating_functions():
    def fn() -> int:
        return 1

    node = Node.from_fn(fn)
    node_copy = node.copy_with(name="rename_fn", originating_functions=(fn,))
    assert node_copy.originating_functions == (fn,)
    assert node_copy.name == "rename_fn"
    node_copy_copy = node_copy.copy_with(name="rename_fn_again")
    assert node_copy_copy.originating_functions == (fn,)
    assert node_copy_copy.name == "rename_fn_again"


np_version = np.__version__
major, minor, _ = map(int, np_version.split("."))


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python 3.9 or higher")
def test_node_handles_annotated():
    from typing import Annotated

    DType = TypeVar("DType", bound=np.generic)
    ArrayN = Annotated[npt.NDArray[DType], Literal["N"]]

    def annotated_func(first: ArrayN[np.float64], other: float = 2.0) -> ArrayN[np.float64]:
        return first * other

    node = Node.from_fn(annotated_func)
    assert node.name == "annotated_func"
    if major == 2 and minor > 1 and sys.version_info > (3, 9):  # greater that 2.1
        expected = {
            "first": (
                Annotated[np.ndarray[tuple[int, ...], np.dtype[np.float64]], Literal["N"]],
                DependencyType.REQUIRED,
            ),
            "other": (float, DependencyType.OPTIONAL),
        }
        expected_type = Annotated[np.ndarray[tuple[int, ...], np.dtype[np.float64]], Literal["N"]]
    else:
        expected = {
            "first": (
                Annotated[np.ndarray[Any, np.dtype[np.float64]], Literal["N"]],
                DependencyType.REQUIRED,
            ),
            "other": (float, DependencyType.OPTIONAL),
        }
        expected_type = Annotated[np.ndarray[Any, np.dtype[np.float64]], Literal["N"]]
    assert node.input_types == expected
    assert node.type == expected_type


@pytest.mark.parametrize(
    "tags, query, expected",
    [
        ({}, {"module": "tests.resources.tagging"}, False),
        ({"module": "tests.resources.tagging"}, {}, True),
        ({"module": "tests.resources.tagging"}, {"module": "tests.resources.tagging"}, True),
        ({"module": "tests.resources.tagging"}, {"module": None}, True),
        ({"module": "tests.resources.tagging"}, {"module": None, "tag2": "value"}, False),
        (
            {"module": "tests.resources.tagging"},
            {"module": "tests.resources.tagging", "tag2": "value"},
            False,
        ),
        ({"tag1": ["tag_value1"]}, {"tag1": "tag_value1"}, True),
        ({"tag1": ["tag_value1"]}, {"tag1": ["tag_value1"]}, True),
        ({"tag1": ["tag_value1"]}, {"tag1": ["tag_value1", "tag_value2"]}, True),
        ({"tag1": "tag_value1"}, {"tag1": ["tag_value1", "tag_value2"]}, True),
        ({"tag1": "tag_value1"}, {"tag1": ["tag_value3", "tag_value4"]}, False),
        ({"tag1": ["tag_value1"]}, {"tag1": "tag_value2"}, False),
        ({"tag1": "tag_value1"}, {"tag1": "tag_value2"}, False),
        ({"tag1": ["tag_value1"]}, {"tag1": ["tag_value2"]}, False),
    ],
    ids=[
        "no tags fail",
        "no query pass",
        "exact match pass",
        "match tag key pass",
        "missing extra tag fail",
        "missing extra tag2 fail",
        "list single match pass",
        "list list match pass",
        "list list match one of pass",
        "single list match one of pass",
        "single list fail",
        "list single fail",
        "single single fail",
        "list list fail",
    ],
)
def test_tags_match_query(tags: dict, query: dict, expected: bool):
    assert matches_query(tags, query) == expected


def test_from_parameter_default_override_equals():
    class BrokenEquals:
        def __eq__(self, other):
            raise ValueError("I'm broken")

    def foo(b: BrokenEquals = BrokenEquals()):  # noqa
        pass

    param = DependencyType.from_parameter(inspect.signature(foo).parameters["b"])
    assert param == DependencyType.OPTIONAL


# Tests parsing for future annotations
# TODO -- we should generalize this but doing this for specific points is OK for now
def test_node_from_future_annotation_parallelizable():
    parallelized = nodes_with_future_annotation.parallelized
    assert node.Node.from_fn(parallelized).node_role == node.NodeType.EXPAND


def test_node_from_future_annotation_standard():
    standard = nodes_with_future_annotation.standard
    assert node.Node.from_fn(standard).node_role == node.NodeType.STANDARD


def test_node_from_future_annotation_collected():
    collected = nodes_with_future_annotation.collected
    assert node.Node.from_fn(collected).node_role == node.NodeType.COLLECT


def test_reassign_inputs():
    def foo(a: int, b: str) -> int:
        return a + len(b)

    node_ = Node.from_fn(foo)

    first_arg_node = node_.reassign_inputs(input_names={"a": "c"})
    new_first_arg = list(first_arg_node.input_types.keys())
    second_arg_node = node_.reassign_inputs(input_names={"b": "d"})
    new_second_arg = list(second_arg_node.input_types.keys())
    both_arg_node = node_.reassign_inputs(input_names={"a": "c", "b": "d"})
    new_both_arg = list(both_arg_node.input_types.keys())
    assert new_first_arg[0] == "c"
    assert new_first_arg[1] == "b"
    assert new_second_arg[0] == "a"
    assert new_second_arg[1] == "d"
    assert new_both_arg[0] == "c"
    assert new_both_arg[1] == "d"
    assert both_arg_node(**{"c": 2, "d": "abc"}) == 5


@pytest.mark.asyncio
async def test_subdag_async():
    async def foo(a: int, b: str) -> int:
        return a + len(b)

    node_ = Node.from_fn(foo)

    new_node = node_.reassign_inputs(input_names={"a": "c", "b": "d"})
    new_args = list(new_node.input_types.keys())
    assert new_args[0] == "c"
    assert new_args[1] == "d"
    assert inspect.iscoroutinefunction(new_node.callable)
    assert await new_node(**{"c": 2, "d": "abc"}) == 5
