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
from typing import List, Set

import pandas as pd
import pytest

import hamilton.function_modifiers
from hamilton import async_driver, base, driver, function_modifiers, models, node
from hamilton.function_modifiers import does
from hamilton.function_modifiers.dependencies import source, value
from hamilton.function_modifiers.macros import (
    Applicable,
    apply_to,
    ensure_function_empty,
    mutate,
    pipe_input,
    pipe_output,
    step,
)
from hamilton.node import DependencyType

import tests.resources.mutate
import tests.resources.mutate_async
import tests.resources.pipe_async
import tests.resources.pipe_input
import tests.resources.pipe_output


def test_no_code_validator():
    def no_code():
        pass

    def no_code_with_docstring():
        """This should still show up as having no code, even though it has a docstring"""
        pass

    def yes_code():
        """This should show up as having no code"""
        a = 0
        return a

    ensure_function_empty(no_code)
    ensure_function_empty(no_code_with_docstring)
    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        ensure_function_empty(yes_code)


# Functions for  @does -- these are the functions we're "replacing"
def _no_params() -> int:
    pass


def _one_param(a: int) -> int:
    pass


def _two_params(a: int, b: int) -> int:
    pass


def _three_params(a: int, b: int, c: int) -> int:
    pass


def _three_params_with_defaults(a: int, b: int = 1, c: int = 2) -> int:
    pass


def _empty() -> int:
    return 1


def _kwargs(**kwargs: int) -> int:
    return sum(kwargs.values())


def _kwargs_with_a(a: int, **kwargs: int) -> int:
    return a + sum(kwargs.values())


def _just_a(a: int) -> int:
    return a


def _just_b(b: int) -> int:
    return b


def _a_b_c(a: int, b: int, c: int) -> int:
    return a + b + c


@pytest.mark.parametrize(
    "fn,replace_with,argument_mapping,matches",
    [
        (_no_params, _empty, {}, True),
        (_no_params, _kwargs, {}, True),
        (_no_params, _kwargs_with_a, {}, False),
        (_no_params, _just_a, {}, False),
        (_no_params, _a_b_c, {}, False),
        (_one_param, _empty, {}, False),
        (_one_param, _kwargs, {}, True),
        (_one_param, _kwargs_with_a, {}, True),
        (_one_param, _just_a, {}, True),
        (_one_param, _just_b, {}, False),
        (_one_param, _just_b, {"b": "a"}, True),  # Replacing a with b makes the signatures match
        (_one_param, _just_b, {"c": "a"}, False),  # Replacing a with b makes the signatures match
        (_two_params, _empty, {}, False),
        (_two_params, _kwargs, {}, True),
        (_two_params, _kwargs_with_a, {}, True),  # b gets fed to kwargs
        (_two_params, _kwargs_with_a, {"foo": "b"}, True),  # Any kwargs work
        (_two_params, _kwargs_with_a, {"bar": "a"}, False),  # No param bar
        (_two_params, _just_a, {}, False),
        (_two_params, _just_b, {}, False),
        (_three_params, _a_b_c, {}, True),
        (_three_params, _a_b_c, {"d": "a"}, False),
        (_three_params, _a_b_c, {}, True),
        (_three_params, _a_b_c, {"a": "b", "b": "a"}, True),  # Weird case but why not?
        (_three_params, _kwargs_with_a, {}, True),
        (_three_params_with_defaults, _a_b_c, {}, True),
        (_three_params_with_defaults, _a_b_c, {"d": "a"}, False),
        (_three_params_with_defaults, _a_b_c, {}, True),
    ],
)
def test_ensure_function_signatures_compatible(fn, replace_with, argument_mapping, matches):
    assert (
        does.test_function_signatures_compatible(
            inspect.signature(fn), inspect.signature(replace_with), argument_mapping
        )
        == matches
    )


def test_does_function_modifier():
    def sum_(**kwargs: int) -> int:
        return sum(kwargs.values())

    def to_modify(param1: int, param2: int) -> int:
        """This sums the inputs it gets..."""
        pass

    annotation = does(sum_)
    (node_,) = annotation.generate_nodes(to_modify, {})
    assert node_.name == "to_modify"
    assert node_.callable(param1=1, param2=1) == 2
    assert node_.documentation == to_modify.__doc__


def test_does_function_modifier_complex_types():
    def setify(**kwargs: List[int]) -> Set[int]:
        return set(sum(kwargs.values(), []))

    def to_modify(param1: List[int], param2: List[int]) -> int:
        """This sums the inputs it gets..."""
        pass

    annotation = does(setify)
    (node_,) = annotation.generate_nodes(to_modify, {})
    assert node_.name == "to_modify"
    assert node_.callable(param1=[1, 2, 3], param2=[4, 5, 6]) == {1, 2, 3, 4, 5, 6}
    assert node_.documentation == to_modify.__doc__


def test_does_function_modifier_optionals():
    def sum_(param0: int, **kwargs: int) -> int:
        return sum(kwargs.values())

    def to_modify(param0: int, param1: int = 1, param2: int = 2) -> int:
        """This sums the inputs it gets..."""
        pass

    annotation = does(sum_)
    (node_,) = annotation.generate_nodes(to_modify, {})
    assert node_.name == "to_modify"
    assert node_.input_types["param0"][1] == DependencyType.REQUIRED
    assert node_.input_types["param1"][1] == DependencyType.OPTIONAL
    assert node_.input_types["param2"][1] == DependencyType.OPTIONAL
    assert node_.callable(param0=0) == 3
    assert node_.callable(param0=0, param1=0, param2=0) == 0
    assert node_.documentation == to_modify.__doc__


def test_does_with_argument_mapping():
    def _sum_multiply(param0: int, param1: int, param2: int) -> int:
        return param0 + param1 * param2

    def to_modify(parama: int, paramb: int = 1, paramc: int = 2) -> int:
        """This sums the inputs it gets..."""
        pass

    annotation = does(_sum_multiply, param0="parama", param1="paramb", param2="paramc")
    (node_,) = annotation.generate_nodes(to_modify, {})
    assert node_.name == "to_modify"
    assert node_.input_types["parama"][1] == DependencyType.REQUIRED
    assert node_.input_types["paramb"][1] == DependencyType.OPTIONAL
    assert node_.input_types["paramc"][1] == DependencyType.OPTIONAL
    assert node_.callable(parama=0) == 2
    assert node_.callable(parama=0, paramb=1, paramc=2) == 2
    assert node_.callable(parama=1, paramb=4) == 9
    assert node_.documentation == to_modify.__doc__


def test_model_modifier():
    config = {
        "my_column_model_params": {
            "col_1": 0.5,
            "col_2": 0.5,
        }
    }

    class LinearCombination(models.BaseModel):
        def get_dependents(self) -> List[str]:
            return list(self.config_parameters.keys())

        def predict(self, **columns: pd.Series) -> pd.Series:
            return sum(
                self.config_parameters[column_name] * column
                for column_name, column in columns.items()
            )

    def my_column() -> pd.Series:
        """Column that will be annotated by a model"""
        pass

    annotation = function_modifiers.model(LinearCombination, "my_column_model_params")
    annotation.validate(my_column)
    (model_node,) = annotation.generate_nodes(my_column, config)
    assert model_node.input_types["col_1"][0] == model_node.input_types["col_2"][0] == pd.Series
    assert model_node.type == pd.Series
    pd.testing.assert_series_equal(
        model_node.callable(col_1=pd.Series([1]), col_2=pd.Series([2])), pd.Series([1.5])
    )

    def bad_model(col_1: pd.Series, col_2: pd.Series) -> pd.Series:
        return col_1 * 0.5 + col_2 * 0.5

    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        annotation.validate(bad_model)


def _test_apply_function(foo: int, bar: int, baz: int = 100) -> int:
    return foo + bar + baz


@pytest.mark.parametrize(
    "args,kwargs,chain_first_param",
    [
        ([source("foo_upstream"), value(1)], {}, False),
        ([value(1)], {}, True),
        ([source("foo_upstream"), value(1), value(2)], {}, False),
        ([value(1), value(2)], {}, True),
        ([source("foo_upstream")], {"bar": value(1)}, False),
        ([], {"bar": value(1)}, True),
        ([], {"foo": source("foo_upstream"), "bar": value(1)}, False),
        ([], {"bar": value(1)}, True),
        ([], {"foo": source("foo_upstream"), "bar": value(1), "baz": value(1)}, False),
        ([], {"bar": value(1), "baz": value(1)}, True),
    ],
)
def test_applicable_validates_correctly(args, kwargs, chain_first_param: bool):
    applicable = Applicable(_test_apply_function, args=args, kwargs=kwargs)
    applicable.validate(chain_first_param=chain_first_param, allow_custom_namespace=True)


@pytest.mark.parametrize(
    "args,kwargs,chain_first_param",
    [
        (
            [source("foo_upstream"), value(1)],
            {"foo": source("foo_upstream")},
            True,
        ),  # We chain the first parameter, not pass it in
        ([value(1)], {}, False),  # Not enough first parameters
        ([source("foo_upstream"), value(1), value(2)], {}, True),
        ([value(2)], {"foo": source("foo_upstream")}, False),
        ([source("foo_upstream")], {"bar": value(1)}, True),
        ([], {"bar": value(1)}, False),
        ([], {"foo": source("foo_upstream"), "bar": value(1)}, True),
        ([], {"bar": value(1)}, False),
        ([], {"foo": source("foo_upstream"), "bar": value(1), "baz": value(1)}, True),
        ([], {"bar": value(1), "baz": value(1)}, False),
    ],
)
def test_applicable_does_not_validate(args, kwargs, chain_first_param: bool):
    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        applicable = Applicable(_test_apply_function, args=args, kwargs=kwargs)
        applicable.validate(chain_first_param=chain_first_param, allow_custom_namespace=True)


def test_applicable_does_not_validate_invalid_function_pos_only():
    def foo(a: int, /, b: int) -> int:
        return a + b

    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        applicable = Applicable(foo, args=(source("a"), source("b")), kwargs={})
        applicable.validate(chain_first_param=True, allow_custom_namespace=True)


# We will likely start supporting this in the future, but for now we don't
def test_applicable_does_not_validate_no_param_type_hints():
    def foo(a, b) -> int:
        return a + b

    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        applicable = Applicable(foo, args=(source("a"), source("b")), kwargs={})
        applicable.validate(chain_first_param=True, allow_custom_namespace=True)


def test_applicable_does_not_validate_no_return_type_hints():
    def foo(a: int, b: int):
        return a + b

    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        applicable = Applicable(foo, args=(source("a"), source("b")), kwargs={})
        applicable.validate(chain_first_param=True, allow_custom_namespace=True)


def test_applicable_does_not_validate_invalid_function_no_params():
    def foo() -> int:
        return 1

    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        applicable = Applicable(foo, args=(), kwargs={})
        applicable.validate(chain_first_param=True, allow_custom_namespace=True)


def general_downstream_function(result: int) -> int:
    return result


def function_multiple_same_type_params(p1: int, p2: int, p3: int) -> int:
    return p1 + p2 + p3


# TODO: in case of multiple paramters need some type checking
# def function_multiple_diverse_type_params(p1: int, p2: str, p3: int) -> int:
#     return p1 + len(p2) + p3


def test_pipe_input_on_input_error_unless_string_or_none():
    with pytest.raises(NotImplementedError):
        decorator = pipe_input(  # noqa
            step(_test_apply_function, source("bar_upstream"), baz=value(10)).named("node_1"),
            step(_test_apply_function, source("bar_upstream"), baz=value(100)).named("node_2"),
            step(_test_apply_function, source("bar_upstream"), baz=value(1000)).named("node_3"),
            on_input=["p2", "p3"],
            namespace="abc",
        )


def test_pipe_input_mapping_args_targets_global():
    n = node.Node.from_fn(function_multiple_same_type_params)

    decorator = pipe_input(
        step(_test_apply_function, source("bar_upstream"), baz=value(10)).named("node_1"),
        step(_test_apply_function, source("bar_upstream"), baz=value(100)).named("node_2"),
        step(_test_apply_function, source("bar_upstream"), baz=value(1000)).named("node_3"),
        on_input="p2",
        namespace="abc",
    )
    nodes = decorator.transform_dag([n], {}, function_multiple_same_type_params)
    nodes_by_name = {item.name: item for item in nodes}
    chain_node = nodes_by_name["abc.node_1"]
    assert chain_node(p2=1, bar_upstream=3) == 14


# TODO: multiple parameter tests
# def test_pipe_input_no_namespace_with_target():
#     n = node.Node.from_fn(function_multiple_diverse_type_params)

#     decorator = pipe_input(
#         step(_test_apply_function, source("bar_upstream"), baz=value(10))
#         .on_input(["p1", "p3"])
#         .named("node_1"),
#         step(_test_apply_function, source("bar_upstream"), baz=value(100)).named("node_2"),
#         step(_test_apply_function, source("bar_upstream"), baz=value(1000))
#         .on_input("p3")
#         .named("node_3"),
#         on_input="p2",
#         namespace=None,
#     )
#     nodes = decorator.transform_dag([n], {}, function_multiple_diverse_type_params)
#     final_node = nodes[0].name
#     p1_node = nodes[1].name
#     p2_node1 = nodes[2].name
#     p2_node2 = nodes[3].name
#     p2_node3 = nodes[4].name
#     p3_node1 = nodes[5].name
#     p3_node2 = nodes[6].name

#     assert final_node == "function_multiple_diverse_type_params"
#     assert p1_node == "p1.node_1"
#     assert p2_node1 == "p2.node_1"
#     assert p2_node2 == "p2.node_2"
#     assert p2_node3 == "p2.node_3"
#     assert p3_node1 == "p3.node_1"
#     assert p3_node2 == "p3.node_3"


# def test_pipe_input_elipsis_namespace_with_target():
#     n = node.Node.from_fn(function_multiple_diverse_type_params)

#     decorator = pipe_input(
#         step(_test_apply_function, source("bar_upstream"), baz=value(10))
#         .on_input(["p1", "p3"])
#         .named("node_1"),
#         step(_test_apply_function, source("bar_upstream"), baz=value(100)).named("node_2"),
#         step(_test_apply_function, source("bar_upstream"), baz=value(1000))
#         .on_input("p3")
#         .named("node_3"),
#         namespace=...,
#         on_input="p2",
#     )
#     nodes = decorator.transform_dag([n], {}, function_multiple_diverse_type_params)
#     final_node = nodes[0].name
#     p1_node = nodes[1].name
#     p2_node1 = nodes[2].name
#     p2_node2 = nodes[3].name
#     p2_node3 = nodes[4].name
#     p3_node1 = nodes[5].name
#     p3_node2 = nodes[6].name

#     assert final_node == "function_multiple_diverse_type_params"
#     assert p1_node == "p1.node_1"
#     assert p2_node1 == "p2.node_1"
#     assert p2_node2 == "p2.node_2"
#     assert p2_node3 == "p2.node_3"
#     assert p3_node1 == "p3.node_1"
#     assert p3_node2 == "p3.node_3"


# def test_pipe_input_custom_namespace_with_target():
#     n = node.Node.from_fn(function_multiple_diverse_type_params)

#     decorator = pipe_input(
#         step(_test_apply_function, source("bar_upstream"), baz=value(10))
#         .on_input(["p1", "p3"])
#         .named("node_1"),
#         step(_test_apply_function, source("bar_upstream"), baz=value(100)).named("node_2"),
#         step(_test_apply_function, source("bar_upstream"), baz=value(1000))
#         .on_input("p3")
#         .named("node_3"),
#         namespace="abc",
#         on_input="p2",
#     )
#     nodes = decorator.transform_dag([n], {}, function_multiple_diverse_type_params)
#     final_node = nodes[0].name
#     p1_node = nodes[1].name
#     p2_node1 = nodes[2].name
#     p2_node2 = nodes[3].name
#     p2_node3 = nodes[4].name
#     p3_node1 = nodes[5].name
#     p3_node2 = nodes[6].name

#     assert final_node == "function_multiple_diverse_type_params"
#     assert p1_node == "abc_p1.node_1"
#     assert p2_node1 == "abc_p2.node_1"
#     assert p2_node2 == "abc_p2.node_2"
#     assert p2_node3 == "abc_p2.node_3"
#     assert p3_node1 == "abc_p3.node_1"
#     assert p3_node2 == "abc_p3.node_3"


# def test_pipe_input_mapping_args_targets_local():
#     n = node.Node.from_fn(function_multiple_diverse_type_params)

#     decorator = pipe_input(
#         step(_test_apply_function, source("bar_upstream"), baz=value(10))
#         .on_input(["p1", "p3"])
#         .named("node_1"),
#         step(_test_apply_function, source("bar_upstream"), baz=value(100))
#         .on_input("p2")
#         .named("node_2"),
#         step(_test_apply_function, source("bar_upstream"), baz=value(1000))
#         .on_input("p3")
#         .named("node_3"),
#         namespace="abc",
#     )
#     nodes = decorator.transform_dag([n], {}, function_multiple_diverse_type_params)
#     nodes_by_name = {item.name: item for item in nodes}
#     chain_node_1 = nodes_by_name["abc_p1.node_1"]
#     chain_node_2 = nodes_by_name["abc_p2.node_2"]
#     chain_node_3_first = nodes_by_name["abc_p3.node_1"]
#     assert chain_node_1(p1=1, bar_upstream=3) == 14
#     assert chain_node_2(p2=1, bar_upstream=3) == 104
#     assert chain_node_3_first(p3=7, bar_upstream=3) == 20
#
#
# def test_pipe_input_mapping_args_targets_local_adds_to_global():
#     n = node.Node.from_fn(function_multiple_same_type_params)

#     decorator = pipe_input(
#         step(_test_apply_function, source("bar_upstream"), baz=value(10))
#         .on_input(["p1", "p2"])
#         .named("node_1"),
#         step(_test_apply_function, source("bar_upstream"), baz=value(100))
#         .on_input("p2")
#         .named("node_2"),
#         step(_test_apply_function, source("bar_upstream"), baz=value(1000)).named("node_3"),
#         on_input="p3",
#         namespace="abc",
#     )
#     nodes = decorator.transform_dag([n], {}, function_multiple_diverse_type_params)
#     nodes_by_name = {item.name: item for item in nodes}
#     p1_node = nodes_by_name["abc_p1.node_1"]
#     p2_node1 = nodes_by_name["abc_p2.node_1"]
#     p2_node2 = nodes_by_name["abc_p2.node_2"]
#     p3_node1 = nodes_by_name["abc_p3.node_1"]
#     p3_node2 = nodes_by_name["abc_p3.node_2"]
#     p3_node3 = nodes_by_name["abc_p3.node_3"]

#     assert p1_node(p1=1, bar_upstream=3) == 14
#     assert p2_node1(p2=7, bar_upstream=3) == 20
#     assert p2_node2(**{"abc_p2.node_1": 2, "bar_upstream": 3}) == 105
#     assert p3_node1(p3=9, bar_upstream=3) == 22
#     assert p3_node2(**{"abc_p3.node_1": 13, "bar_upstream": 3}) == 116
#     assert p3_node3(**{"abc_p3.node_2": 17, "bar_upstream": 3}) == 1020


# def test_pipe_input_fails_with_missing_targets():
#     n = node.Node.from_fn(function_multiple_same_type_params)

#     decorator = pipe_input(
#         step(_test_apply_function, source("bar_upstream"), baz=value(10))
#         .on_input(["p1", "p2"])
#         .named("node_1"),
#         step(_test_apply_function, source("bar_upstream"), baz=value(100))
#         .on_input("p2")
#         .named("node_2"),
#         step(_test_apply_function, source("bar_upstream"), baz=value(1000)).named("node_3"),
#         namespace="abc",
#     )
#     with pytest.raises(hamilton.function_modifiers.macros.MissingTargetError):
#         nodes = decorator.transform_dag([n], {}, function_multiple_same_type_params)  # noqa


# def test_pipe_input_decorator_with_target_no_collapse_multi_node():
#     n = node.Node.from_fn(function_multiple_same_type_params)

#     decorator = pipe_input(
#         step(_test_apply_function, source("bar_upstream"), baz=value(10))
#         .on_input(["p1", "p3"])
#         .named("node_1"),
#         step(_test_apply_function, source("bar_upstream"), baz=value(100))
#         .on_input("p2")
#         .named("node_2"),
#         step(_test_apply_function, source("bar_upstream"), baz=value(1000))
#         .on_input("p3")
#         .named("node_3"),
#         namespace="abc",
#     )
#     nodes = decorator.transform_dag([n], {}, function_multiple_diverse_type_params)
#     nodes_by_name = {item.name: item for item in nodes}
#     final_node = nodes_by_name["function_multiple_same_type_params"]
#     chain_node_1 = nodes_by_name["abc_p1.node_1"]
#     chain_node_2 = nodes_by_name["abc_p2.node_2"]
#     chain_node_3_first = nodes_by_name["abc_p3.node_1"]
#     chain_node_3_second = nodes_by_name["abc_p3.node_3"]
#     assert len(nodes_by_name) == 5
#     assert chain_node_1(p1=1, bar_upstream=3) == 14
#     assert chain_node_2(p2=1, bar_upstream=3) == 104
#     assert chain_node_3_first(p3=7, bar_upstream=3) == 20
#     assert chain_node_3_second(**{"abc_p3.node_1": 13, "bar_upstream": 3}) == 1016
#     assert final_node(**{"abc_p1.node_1": 3, "abc_p2.node_2": 4, "abc_p3.node_3": 5}) == 12


def test_pipe_decorator_positional_variable_args():
    n = node.Node.from_fn(general_downstream_function)

    decorator = pipe_input(
        step(_test_apply_function, source("bar_upstream"), baz=value(1000)).named("node_1"),
        namespace=None,
    )
    nodes = decorator.transform_dag([n], {}, general_downstream_function)
    nodes_by_name = {item.name: item for item in nodes}
    chain_node = nodes_by_name["node_1"]
    assert chain_node(result=1, bar_upstream=10) == 1011  # This chains it through
    assert sorted(chain_node.input_types) == ["bar_upstream", "result"]
    final_node = nodes_by_name["general_downstream_function"]
    assert final_node(node_1=1) == 1


def test_pipe_decorator_no_collapse_multi_node():
    n = node.Node.from_fn(general_downstream_function)

    decorator = pipe_input(
        step(_test_apply_function, bar=source("bar_upstream"), baz=100).named("node_1"),
        step(_test_apply_function, bar=value(10), baz=value(100)).named("node_2"),
        namespace=None,
    )
    nodes = decorator.transform_dag([n], {}, general_downstream_function)
    nodes_by_name = {item.name: item for item in nodes}
    final_node = nodes_by_name["general_downstream_function"]
    assert len(nodes_by_name) == 3
    assert nodes_by_name["node_1"](result=1, bar_upstream=10) == 111
    assert nodes_by_name["node_2"](node_1=1) == 111
    assert final_node(node_2=100) == 100


def test_resolve_namespace_inherit():
    applicable = Applicable(
        _test_apply_function, args=(), kwargs=dict(bar=source("bar_upstream"), baz=100)
    ).named("node_1")
    assert applicable.resolve_namespace("inherited") == ("inherited",)


def test_resolve_namespace_discard():
    applicable = Applicable(
        _test_apply_function, args=(), kwargs=dict(bar=source("bar_upstream"), baz=100)
    ).named("node_1", namespace=None)
    assert applicable.resolve_namespace("unused") == ()


def test_resolve_namespace_replaced():
    applicable = Applicable(
        _test_apply_function, args=(), kwargs=dict(bar=source("bar_upstream"), baz=100)
    ).named("node_1", namespace="replaced")
    assert applicable.resolve_namespace("unused") == ("replaced",)


def test_validate_pipe_fails_with_conflicting_namespace():
    decorator = pipe_input(
        step(_test_apply_function, bar=source("bar_upstream"), baz=100).named(
            "node_1", namespace="custom"
        ),
        namespace=None,  # Not allowed to have custom namespacess if the namespace is None
    )
    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        decorator.validate(general_downstream_function)


def test_inherits_null_namespace():
    n = node.Node.from_fn(general_downstream_function)
    decorator = pipe_input(
        step(_test_apply_function, bar=source("bar_upstream"), baz=100).named(
            "node_1", namespace=...
        ),
        namespace=None,  # Not allowed to have custom namespacess if the namespace is None
    )
    decorator.validate(general_downstream_function)
    nodes = decorator.transform_dag([n], {}, general_downstream_function)
    assert "node_1" in {item.name for item in nodes}
    assert "general_downstream_function" in {item.name for item in nodes}


def test_pipe_end_to_end_1():
    dr = (
        driver.Builder()
        .with_modules(tests.resources.pipe_input)
        .with_adapter(base.DefaultAdapter())
        .with_config({"calc_c": True})
        .build()
    )

    inputs = {
        "input_1": 10,
        "input_2": 20,
        "input_3": 30,
    }
    result = dr.execute(
        [
            "chain_1_using_pipe",
            "chain_2_using_pipe",
            "chain_1_not_using_pipe",
            "chain_2_not_using_pipe",
        ],
        inputs=inputs,
    )
    assert result["chain_1_using_pipe"] == result["chain_1_not_using_pipe"]
    assert result["chain_2_using_pipe"] == result["chain_2_not_using_pipe"]


def test_pipe_end_to_end_target_global():
    dr = (
        driver.Builder()
        .with_modules(tests.resources.pipe_input)
        .with_adapter(base.DefaultAdapter())
        .with_config({"calc_c": True})
        .build()
    )

    inputs = {
        "input_1": 10,
        "input_2": 20,
        "input_3": 30,
    }
    result = dr.execute(
        [
            "chain_1_using_pipe_input_target_global",
            "chain_1_not_using_pipe_input_target_global",
        ],
        inputs=inputs,
    )
    assert (
        result["chain_1_not_using_pipe_input_target_global"]
        == result["chain_1_using_pipe_input_target_global"]
    )


# TODO: For multiple parameters end-to-end
# def test_pipe_end_to_end_target_local():
#     dr = (
#         driver.Builder()
#         .with_modules(tests.resources.pipe_input)
#         .with_adapter(base.DefaultAdapter())
#         .with_config({"calc_c": True})
#         .build()
#     )

#     inputs = {
#         "input_1": 10,
#         "input_2": 20,
#         "input_3": 30,
#     }
#     result = dr.execute(
#         [
#             "chain_1_using_pipe_input_target_local",
#             "chain_1_not_using_pipe_input_target_local",
#         ],
#         inputs=inputs,
#     )
#     assert (
#         result["chain_1_not_using_pipe_input_target_local"]
#         == result["chain_1_using_pipe_input_target_local"]
#     )

# def test_pipe_end_to_end_target_mixed():
#     dr = (
#         driver.Builder()
#         .with_modules(tests.resources.pipe_input)
#         .with_adapter(base.DefaultAdapter())
#         .with_config({"calc_c": True})
#         .build()
#     )

#     inputs = {
#         "input_1": 10,
#         "input_2": 20,
#         "input_3": 30,
#     }
#     result = dr.execute(
#         [
#             "chain_1_using_pipe_input_target_mixed",
#             "chain_1_not_using_pipe_input_target_mixed",
#         ],
#         inputs=inputs,
#     )
#     assert (
#         result["chain_1_not_using_pipe_input_target_mixed"]
#         == result["chain_1_using_pipe_input_target_mixed"]
#     )


def result_from_downstream_function() -> int:
    return 2


def test_pipe_output_single_target_level_error():
    with pytest.raises(hamilton.function_modifiers.macros.SingleTargetError):
        pipe_output(
            step(_test_apply_function, source("bar_upstream"), baz=value(100)).on_output(
                "some_node"
            ),
            on_output="some_other_node",
        )


def test_pipe_output_shortcircuit():
    n = node.Node.from_fn(result_from_downstream_function)
    decorator = pipe_output()
    nodes = decorator.transform_dag([n], {}, result_from_downstream_function)
    assert len(nodes) == 1
    assert n == nodes[0]


def test_pipe_output_decorator_positional_single_node():
    n = node.Node.from_fn(result_from_downstream_function)

    decorator = pipe_output(
        step(_test_apply_function, source("bar_upstream"), baz=value(100)).named("node_1"),
        namespace=None,
    )
    nodes = decorator.transform_dag([n], {}, result_from_downstream_function)
    nodes_by_name = {item.name: item for item in nodes}
    chain_node = nodes_by_name["node_1"]
    assert chain_node(**{"result_from_downstream_function.raw": 2, "bar_upstream": 10}) == 112
    assert sorted(chain_node.input_types) == [
        "bar_upstream",
        "result_from_downstream_function.raw",
    ]
    final_node = nodes_by_name["result_from_downstream_function"]
    assert final_node(foo=112) == 112  # original arg name
    assert final_node(node_1=112) == 112  # renamed to match the last node


def test_pipe_output_decorator_no_collapse_multi_node():
    n = node.Node.from_fn(result_from_downstream_function)

    decorator = pipe_output(
        step(_test_apply_function, bar=source("bar_upstream"), baz=100).named("node_1"),
        step(_test_apply_function, bar=value(10), baz=value(100)).named("node_2"),
        namespace=None,
    )
    nodes = decorator.transform_dag([n], {}, result_from_downstream_function)
    nodes_by_name = {item.name: item for item in nodes}
    final_node = nodes_by_name["result_from_downstream_function"]
    assert len(nodes_by_name) == 4  # We add fn_raw and identity
    assert (
        nodes_by_name["node_1"](**{"result_from_downstream_function.raw": 1, "bar_upstream": 10})
        == 111
    )
    assert nodes_by_name["node_2"](node_1=4) == 114
    assert final_node(node_2=13) == 13


def test_validate_pipe_output_fails_with_conflicting_namespace():
    decorator = pipe_output(
        step(_test_apply_function, bar=source("bar_upstream"), baz=100).named(
            "node_1", namespace="custom"
        ),
        namespace=None,  # Not allowed to have custom namespacess if the namespace is None
    )
    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        decorator.validate(result_from_downstream_function)


def test_pipe_output_inherits_null_namespace():
    n = node.Node.from_fn(result_from_downstream_function)
    decorator = pipe_output(
        step(_test_apply_function, bar=source("bar_upstream"), baz=100).named(
            "node_1", namespace=...
        ),
        namespace=None,  # Not allowed to have custom namespacess if the namespace is None
    )
    decorator.validate(result_from_downstream_function)
    nodes = decorator.transform_dag([n], {}, result_from_downstream_function)
    assert "node_1" in {item.name for item in nodes}
    assert "result_from_downstream_function.raw" in {item.name for item in nodes}
    assert "result_from_downstream_function" in {item.name for item in nodes}


def test_pipe_output_global_on_output_all():
    n1 = node.Node.from_fn(result_from_downstream_function, name="node_1")
    n2 = node.Node.from_fn(result_from_downstream_function, name="node_2")

    decorator = pipe_output(
        step(_test_apply_function, source("bar_upstream"), baz=value(100)),
    )
    nodes = decorator.select_nodes(decorator.target, [n1, n2])
    assert len(nodes) == 2
    assert [node_.name for node_ in nodes] == ["node_1", "node_2"]


def test_pipe_output_global_on_output_string():
    n1 = node.Node.from_fn(result_from_downstream_function, name="node_1")
    n2 = node.Node.from_fn(result_from_downstream_function, name="node_2")

    decorator = pipe_output(
        step(_test_apply_function, source("bar_upstream"), baz=value(100)), on_output="node_2"
    )
    nodes = decorator.select_nodes(decorator.target, [n1, n2])
    assert len(nodes) == 1
    assert nodes[0].name == "node_2"


def test_pipe_output_global_on_output_list_strings():
    n1 = node.Node.from_fn(result_from_downstream_function, name="node_1")
    n2 = node.Node.from_fn(result_from_downstream_function, name="node_2")
    n3 = node.Node.from_fn(result_from_downstream_function, name="node_3")

    decorator = pipe_output(
        step(_test_apply_function, source("bar_upstream"), baz=value(100)),
        on_output=["node_1", "node_2"],
    )
    nodes = decorator.select_nodes(decorator.target, [n1, n2, n3])
    assert len(nodes) == 2
    assert [node_.name for node_ in nodes] == ["node_1", "node_2"]


def test_pipe_output_elipsis_error():
    with pytest.raises(ValueError):
        pipe_output(
            step(_test_apply_function, source("bar_upstream"), baz=value(100)), on_output=...
        )


def test_pipe_output_local_on_output_string():
    n1 = node.Node.from_fn(result_from_downstream_function, name="node_1")
    n2 = node.Node.from_fn(result_from_downstream_function, name="node_2")

    decorator = pipe_output(
        step(_test_apply_function, source("bar_upstream"), baz=value(100))
        .named("correct_transform")
        .on_output("node_2"),
        step(_test_apply_function, source("bar_upstream"), baz=value(100))
        .named("wrong_transform")
        .on_output("node_3"),
    )
    steps = decorator._filter_individual_target(n1)
    assert len(steps) == 0
    steps = decorator._filter_individual_target(n2)
    assert len(steps) == 1
    assert steps[0].name == "correct_transform"


def test_pipe_output_local_on_output_list_string():
    n1 = node.Node.from_fn(result_from_downstream_function, name="node_1")
    n2 = node.Node.from_fn(result_from_downstream_function, name="node_2")
    n3 = node.Node.from_fn(result_from_downstream_function, name="node_3")

    decorator = pipe_output(
        step(_test_apply_function, source("bar_upstream"), baz=value(100))
        .named("correct_transform_list")
        .on_output(["node_2", "node_3"]),
        step(_test_apply_function, source("bar_upstream"), baz=value(100))
        .named("correct_transform_string")
        .on_output("node_2"),
        step(_test_apply_function, source("bar_upstream"), baz=value(100))
        .named("wrong_transform")
        .on_output("node_5"),
    )
    steps = decorator._filter_individual_target(n1)
    assert len(steps) == 0
    steps = decorator._filter_individual_target(n2)
    assert len(steps) == 2
    assert steps[0].name == "correct_transform_list"
    assert steps[1].name == "correct_transform_string"
    steps = decorator._filter_individual_target(n3)
    assert len(steps) == 1
    assert steps[0].name == "correct_transform_list"


def test_pipe_output_end_to_end_simple():
    dr = driver.Builder().with_config({"calc_c": True}).build()

    dr = (
        driver.Builder()
        .with_modules(tests.resources.pipe_output)
        .with_adapter(base.DefaultAdapter())
        .build()
    )

    inputs = {}
    result = dr.execute(
        [
            "downstream_f",
            "chain_not_using_pipe_output",
        ],
        inputs=inputs,
    )
    assert result["downstream_f"] == result["chain_not_using_pipe_output"]


def test_pipe_output_end_to_end():
    dr = (
        driver.Builder()
        .with_modules(tests.resources.pipe_output)
        .with_adapter(base.DefaultAdapter())
        .with_config({"calc_c": True})
        .build()
    )

    inputs = {
        "input_1": 10,
        "input_2": 20,
        "input_3": 30,
    }
    result = dr.execute(
        [
            "chain_1_using_pipe_output",
            "chain_2_using_pipe_output",
            "chain_1_not_using_pipe_output",
            "chain_2_not_using_pipe_output",
        ],
        inputs=inputs,
    )
    assert result["chain_1_using_pipe_output"] == result["chain_1_not_using_pipe_output"]
    assert result["chain_2_using_pipe_output"] == result["chain_2_not_using_pipe_output"]


def test_pipe_output_end_to_end_with_config():
    inputs = {
        "input_1": 10,
        "input_2": 20,
        "input_3": 30,
    }

    dr = (
        driver.Builder()
        .with_modules(tests.resources.pipe_output)
        .with_adapter(base.DefaultAdapter())
        .with_config({"key": "Yes"})
        .build()
    )

    result = dr.execute(
        [
            "chain_3_using_pipe_output",
            "chain_3_not_using_pipe_output_config_true",
        ],
        inputs=inputs,
    )
    assert (
        result["chain_3_using_pipe_output"] == result["chain_3_not_using_pipe_output_config_true"]
    )

    dr = (
        driver.Builder()
        .with_modules(tests.resources.pipe_output)
        .with_adapter(base.DefaultAdapter())
        .with_config({"key": "No"})
        .build()
    )

    result = dr.execute(
        [
            "chain_3_using_pipe_output",
            "chain_3_not_using_pipe_output_config_false",
        ],
        inputs=inputs,
    )
    assert (
        result["chain_3_using_pipe_output"] == result["chain_3_not_using_pipe_output_config_false"]
    )

    dr = (
        driver.Builder()
        .with_modules(tests.resources.pipe_output)
        .with_adapter(base.DefaultAdapter())
        .with_config({"key": "skip"})
        .build()
    )
    result = dr.execute(
        [
            "chain_3_using_pipe_output",
            "chain_3_not_using_pipe_output_config_no_conditions_met",
        ],
        inputs=inputs,
    )
    assert (
        result["chain_3_using_pipe_output"]
        == result["chain_3_not_using_pipe_output_config_no_conditions_met"]
    )


# Mutate will mark the modules (and leave a mark).
# Thus calling it a second time (for instance through pmultiple tests) might mess it up slightly...
# Using fixtures just to be sure.


@pytest.fixture(scope="function")
def _downstream_result_to_mutate():
    def downstream_result_to_mutate() -> int:
        return 2

    yield downstream_result_to_mutate


@pytest.fixture(scope="function")
def import_mutate_module():
    import importlib

    mod = importlib.import_module("tests.resources.mutate")
    yield mod


# This doesn't change so no need to have it as fixture
def mutator_function(input_1: int, input_2: int) -> int:
    return input_1 + input_2


def test_mutate_convert_callable_to_applicable(_downstream_result_to_mutate):
    decorator = mutate(_downstream_result_to_mutate)

    assert len(decorator.remote_applicables) == 1
    remote_applicable = decorator.remote_applicables[0]
    assert isinstance(remote_applicable, Applicable)
    assert remote_applicable.fn is None
    assert remote_applicable.target_fn == _downstream_result_to_mutate


def test_mutate_restricted_to_same_module():
    decorator = mutate(tests.resources.mutate.f_of_interest)

    with pytest.raises(hamilton.function_modifiers.macros.NotSameModuleError):
        decorator.validate_same_module(mutator_function)


def test_mutate_global_kwargs(_downstream_result_to_mutate):
    decorator = mutate(apply_to(_downstream_result_to_mutate), input_2=17)
    remote_applicable = decorator.remote_applicables[0]

    pipe_step = decorator._create_step(
        mutating_fn=mutator_function, remote_applicable_builder=remote_applicable
    )
    assert pipe_step.kwargs["input_2"] == 17


def test_mutate_local_kwargs_override_global_ones(_downstream_result_to_mutate):
    decorator = mutate(apply_to(_downstream_result_to_mutate, input_2=13), input_2=17)
    remote_applicable = decorator.remote_applicables[0]

    pipe_step = decorator._create_step(
        mutating_fn=mutator_function, remote_applicable_builder=remote_applicable
    )
    assert pipe_step.kwargs["input_2"] == 13


def test_mutate_end_to_end_simple(import_mutate_module):
    dr = driver.Builder().with_config({"calc_c": True}).build()

    dr = (
        driver.Builder()
        .with_modules(import_mutate_module)
        .with_adapter(base.DefaultAdapter())
        .build()
    )

    inputs = {}
    result = dr.execute(
        [
            "downstream_f",
            "chain_not_using_mutate",
        ],
        inputs=inputs,
    )
    assert result["downstream_f"] == result["chain_not_using_mutate"]


def test_mutate_end_to_end_1(import_mutate_module):
    dr = (
        driver.Builder()
        .with_modules(import_mutate_module)
        .with_adapter(base.DefaultAdapter())
        .with_config({"calc_c": True})
        .build()
    )

    inputs = {
        "input_1": 10,
        "input_2": 20,
        "input_3": 30,
    }
    result = dr.execute(
        [
            "chain_1_using_mutate",
            "chain_2_using_mutate",
            "chain_1_not_using_mutate",
            "chain_2_not_using_mutate",
        ],
        inputs=inputs,
    )
    assert result["chain_1_using_mutate"] == result["chain_1_not_using_mutate"]
    assert result["chain_2_using_mutate"] == result["chain_2_not_using_mutate"]


@pytest.mark.asyncio
async def test_async_pipe_input_and_output_end_to_end():
    inputs = {"data_input": pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})}

    group_by_a = inputs["data_input"].groupby("a").sum().reset_index()
    group_by_b = inputs["data_input"].groupby("b").sum().reset_index()

    dr = (
        await async_driver.Builder()
        .with_modules(tests.resources.pipe_async)
        .with_config(dict(groupby="a"))
        .build()
    )
    results = await dr.execute(final_vars=["data_pipe_input", "data_pipe_output"], inputs=inputs)

    pd.testing.assert_frame_equal(group_by_a, results["data_pipe_output"])
    pd.testing.assert_frame_equal(group_by_a, results["data_pipe_input"])

    dr = (
        await async_driver.Builder()
        .with_modules(tests.resources.pipe_async)
        .with_config(dict(groupby="b"))
        .build()
    )
    results = await dr.execute(final_vars=["data_pipe_input", "data_pipe_output"], inputs=inputs)

    pd.testing.assert_frame_equal(group_by_b, results["data_pipe_output"])
    pd.testing.assert_frame_equal(group_by_b, results["data_pipe_input"])


@pytest.mark.asyncio
async def test_async_mutate_end_to_end():
    inputs = {"data_input": pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})}

    group_by_a = inputs["data_input"].groupby("a").sum().reset_index()
    group_by_b = inputs["data_input"].groupby("b").sum().reset_index()

    dr = (
        await async_driver.Builder()
        .with_modules(tests.resources.mutate_async)
        .with_config(dict(groupby="a"))
        .build()
    )
    results = await dr.execute(final_vars=["data_mutate"], inputs=inputs)

    pd.testing.assert_frame_equal(group_by_a, results["data_mutate"])

    dr = (
        await async_driver.Builder()
        .with_modules(tests.resources.mutate_async)
        .with_config(dict(groupby="b"))
        .build()
    )
    results = await dr.execute(final_vars=["data_mutate"], inputs=inputs)

    pd.testing.assert_frame_equal(group_by_b, results["data_mutate"])
