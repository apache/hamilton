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

import functools
import inspect
import sys
from collections.abc import Callable
from decimal import Decimal
from typing import Any, Literal, TypeVar

import numpy as np
import numpy.typing as npt
import pytest
from packaging.version import Version

from hamilton import node
from hamilton.node import DependencyType, Node, matches_query

from tests.resources import (
    nodes_behind_wrappers,
    nodes_with_future_annotation,
    wrappers_from_another_module,
)


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


np_version = Version(np.__version__)
major, minor = np_version.major, np_version.minor


def test_node_handles_annotated():
    from typing import Annotated

    DType = TypeVar("DType", bound=np.generic)
    ArrayN = Annotated[npt.NDArray[DType], Literal["N"]]

    def annotated_func(first: ArrayN[np.float64], other: float = 2.0) -> ArrayN[np.float64]:
        return first * other

    node = Node.from_fn(annotated_func)
    assert node.name == "annotated_func"
    if major == 2 and 2 <= minor <= 3:  # numpy 2.2-2.3
        expected = {
            "first": (
                Annotated[np.ndarray[tuple[int, ...], np.dtype[np.float64]], Literal["N"]],
                DependencyType.REQUIRED,
            ),
            "other": (float, DependencyType.OPTIONAL),
        }
        expected_type = Annotated[np.ndarray[tuple[int, ...], np.dtype[np.float64]], Literal["N"]]
    elif (major, minor) >= (2, 5):
        expected = {
            "first": (
                Annotated[npt.NDArray[np.float64], Literal["N"]],
                DependencyType.REQUIRED,
            ),
            "other": (float, DependencyType.OPTIONAL),
        }
        expected_type = Annotated[npt.NDArray[np.float64], Literal["N"]]
    elif (major, minor) >= (2, 4):  # numpy 2.4+
        expected = {
            "first": (
                Annotated[np.ndarray[tuple[Any, ...], np.dtype[np.float64]], Literal["N"]],
                DependencyType.REQUIRED,
            ),
            "other": (float, DependencyType.OPTIONAL),
        }
        expected_type = Annotated[np.ndarray[tuple[Any, ...], np.dtype[np.float64]], Literal["N"]]
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
    ("tags", "query", "expected"),
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


# Tests hint resolution for functions with postponed annotations behind a wrapper that another
# module defines. The annotations name `Decimal`, which only the decorated functions' module
# imports, so resolving them against the wrapper's module raises NameError.
@pytest.mark.parametrize(
    ("function_name", "expected_input_types"),
    [
        pytest.param("price", {"amount": Decimal}, id="undecorated"),
        pytest.param(
            "price_with_tax", {"price": Decimal, "tax_rate": Decimal}, id="functools.wraps"
        ),
        pytest.param("price_rounded", {"price_with_tax": Decimal}, id="two-wrapper-layers"),
        pytest.param(
            "price_discounted", {"price_rounded": Decimal}, id="wrapper-hides-a-parameter"
        ),
        pytest.param(
            "price_total",
            {"price_discounted": Decimal, "factor": int},
            id="wrapper-adds-a-parameter-and-its-annotation",
        ),
    ],
)
def test_node_from_future_annotation_behind_wrapper_from_another_module(
    function_name: str, expected_input_types: dict[str, type]
):
    fn = getattr(nodes_behind_wrappers, function_name)

    node_ = Node.from_fn(fn)

    assert node_.type is Decimal
    assert node_.input_types == {
        name: (type_, DependencyType.REQUIRED) for name, type_ in expected_input_types.items()
    }


def test_node_from_wrapper_without_wraps_resolves_against_the_wrapper_module():
    """Without ``functools.wraps`` the wrapper's own annotations are the node's types."""
    fn = wrappers_from_another_module.typed_without_wraps(nodes_behind_wrappers.price)

    node_ = Node.from_fn(fn)

    wrapper_type = wrappers_from_another_module.DefinedOnlyInWrapperModule
    assert node_.type is wrapper_type
    assert node_.input_types == {"value": (wrapper_type, DependencyType.REQUIRED)}


def test_node_from_wrapper_without_wraps_or_annotations_is_rejected():
    fn = wrappers_from_another_module.untyped_without_wraps(nodes_behind_wrappers.price)

    with pytest.raises(ValueError, match="Missing type hint for return value"):
        Node.from_fn(fn)


def test_node_from_bound_method_of_callable_object_with_future_annotation():
    converter = nodes_behind_wrappers.Converter(rate=Decimal(2))

    node_ = Node.from_fn(converter.__call__, name="price_converted")

    assert node_.type is Decimal
    assert node_.input_types == {"price": (Decimal, DependencyType.REQUIRED)}
    assert node_(price=Decimal("1.5")) == Decimal(3)


def test_node_from_partial_of_wrapped_function_with_given_input_types():
    """A ``functools.partial`` carries no annotations; the caller states the remaining inputs."""
    callabl = functools.partial(nodes_behind_wrappers.price_with_tax, tax_rate=Decimal("0.5"))

    node_ = Node("price_with_tax", Decimal, callabl=callabl, input_types={"price": Decimal})

    assert node_.input_types == {"price": (Decimal, DependencyType.REQUIRED)}
    assert node_(price=Decimal(10)) == Decimal(15)


@pytest.mark.parametrize(
    "callabl",
    [
        pytest.param(
            functools.partial(nodes_behind_wrappers.price_with_tax, tax_rate=Decimal("0.5")),
            id="functools.partial",
        ),
        pytest.param(nodes_behind_wrappers.Converter(rate=Decimal(2)), id="callable-object"),
    ],
)
def test_node_from_callable_without_annotations_reports_the_missing_hints(callabl: Callable):
    """Neither a partial nor an instance carries annotations, so its inputs cannot be inferred.

    Python 3.11 to 3.13 reject such an object in ``typing.get_type_hints`` with a TypeError that
    names it; 3.14 and newer return no hints, and Hamilton reports the first parameter without
    one. Neither is an AttributeError about a missing ``__globals__``.
    """
    if sys.version_info >= (3, 14):
        expected = pytest.raises(ValueError, match="Missing type hint for price in function")
    else:
        expected = pytest.raises(TypeError, match="is not a module, class, method, or function")
    with expected:
        Node("price_converted", Decimal, callabl=callabl)


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
