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
import pathlib
import uuid
from itertools import permutations
from typing import List

import pandas as pd
import pytest

import hamilton.graph_utils
import hamilton.htypes
from hamilton import ad_hoc_utils, base, graph, node
from hamilton.execution import graph_functions
from hamilton.function_modifiers import schema
from hamilton.lifecycle import base as lifecycle_base
from hamilton.node import NodeType

import tests.resources.bad_functions
import tests.resources.compatible_input_types
import tests.resources.config_modifier
import tests.resources.cyclic_functions
import tests.resources.dummy_functions
import tests.resources.dummy_functions_module_override
import tests.resources.extract_column_nodes
import tests.resources.extract_columns_execution_count
import tests.resources.functions_with_generics
import tests.resources.incompatible_input_types
import tests.resources.layered_decorators
import tests.resources.multiple_decorators_together
import tests.resources.optional_dependencies
import tests.resources.parametrized_inputs
import tests.resources.parametrized_nodes
import tests.resources.test_default_args
import tests.resources.typing_vs_not_typing


def test_find_functions():
    """Tests that we filter out _ functions when passed a module and don't pull in anything from the imports."""
    expected = [
        ("A", tests.resources.dummy_functions.A),
        ("B", tests.resources.dummy_functions.B),
        ("C", tests.resources.dummy_functions.C),
    ]
    actual = hamilton.graph_utils.find_functions(tests.resources.dummy_functions)
    assert len(actual) == len(expected)
    assert actual == expected


def test_find_functions_from_temporary_function_module():
    """Tests that we handle the TemporaryFunctionModule object correctly."""
    expected = [
        ("A", tests.resources.dummy_functions.A),
        ("B", tests.resources.dummy_functions.B),
        ("C", tests.resources.dummy_functions.C),
    ]
    func_module = ad_hoc_utils.create_temporary_module(
        tests.resources.dummy_functions.A,
        tests.resources.dummy_functions.B,
        tests.resources.dummy_functions.C,
    )
    actual = hamilton.graph_utils.find_functions(func_module)
    assert len(actual) == len(expected)
    assert [node_name for node_name, _ in actual] == [node_name for node_name, _ in expected]
    assert [fn.__code__ for _, fn in actual] == [
        fn.__code__ for _, fn in expected
    ]  # easy way to say they're the same


def test_add_dependency_missing_param_type():
    """Tests case that we error if types are missing from a parameter."""
    with pytest.raises(ValueError):
        a_sig = inspect.signature(tests.resources.bad_functions.A)
        node.Node(
            "A", a_sig.return_annotation, "A doc", tests.resources.bad_functions.A
        )  # should error out


def test_add_dependency_missing_function_type():
    """Tests case that we error if types are missing from a function."""
    with pytest.raises(ValueError):
        b_sig = inspect.signature(tests.resources.bad_functions.B)
        node.Node(
            "B", b_sig.return_annotation, "B doc", tests.resources.bad_functions.B
        )  # should error out


def test_add_dependency_strict_node_dependencies():
    """Tests that we add node dependencies between functions correctly.

    Setup here is: B depends on A. So A is depended on by B. B is not depended on by anyone.
    """
    b_sig = inspect.signature(tests.resources.dummy_functions.B)
    func_node = node.Node("B", b_sig.return_annotation, "B doc", tests.resources.dummy_functions.B)
    func_name = "B"
    nodes = {
        "A": node.Node(
            "A",
            inspect.signature(tests.resources.dummy_functions.A).return_annotation,
            "A doc",
            tests.resources.dummy_functions.A,
        )
    }
    param_name = "A"
    param_type = b_sig.parameters["A"].annotation

    graph.add_dependency(
        func_node,
        func_name,
        nodes,
        param_name,
        param_type,
        lifecycle_base.LifecycleAdapterSet(),
    )
    assert nodes["A"] == func_node.dependencies[0]
    assert func_node.depended_on_by == []


def test_add_dependency_input_nodes_mismatch_on_types():
    """Tests that if two functions request an input that has incompatible types, we error out."""
    b_sig = inspect.signature(tests.resources.incompatible_input_types.b)
    c_sig = inspect.signature(tests.resources.incompatible_input_types.c)

    nodes = {
        "b": node.Node.from_fn(tests.resources.incompatible_input_types.b),
        "c": node.Node.from_fn(tests.resources.incompatible_input_types.c),
    }
    nodes["b"]._originating_functions = (tests.resources.incompatible_input_types.b,)
    nodes["c"]._originating_functions = (tests.resources.incompatible_input_types.c,)
    param_name = "a"

    # this adds 'a' to nodes
    graph.add_dependency(
        nodes["b"],
        "b",
        nodes,
        param_name,
        b_sig.parameters[param_name].annotation,
        lifecycle_base.LifecycleAdapterSet(),
    )

    assert "a" in nodes

    # adding dependency of c on a should fail because the types are incompatible
    with pytest.raises(ValueError):
        graph.add_dependency(
            nodes["c"],
            "c",
            nodes,
            param_name,
            c_sig.parameters[param_name].annotation,
            lifecycle_base.LifecycleAdapterSet(),
        )


def test_add_dependency_input_nodes_mismatch_on_types_complex():
    """Tests a more complex scenario we don't support right now with input types."""
    e_sig = inspect.signature(tests.resources.incompatible_input_types.e)
    f_sig = inspect.signature(tests.resources.incompatible_input_types.f)

    nodes = {
        "e": node.Node.from_fn(tests.resources.incompatible_input_types.e),
        "f": node.Node.from_fn(tests.resources.incompatible_input_types.f),
    }
    nodes["e"]._originating_functions = (tests.resources.incompatible_input_types.e,)
    nodes["f"]._originating_functions = (tests.resources.incompatible_input_types.f,)
    param_name = "d"

    # this adds 'a' to nodes
    graph.add_dependency(
        nodes["e"],
        "e",
        nodes,
        param_name,
        e_sig.parameters[param_name].annotation,
        lifecycle_base.LifecycleAdapterSet(),
    )

    assert "d" in nodes

    # adding dependency of c on a should fail because the types are incompatible
    with pytest.raises(ValueError):
        graph.add_dependency(
            nodes["e"],
            "e",
            nodes,
            param_name,
            f_sig.parameters[param_name].annotation,
            lifecycle_base.LifecycleAdapterSet(),
        )


def test_add_dependency_input_nodes_compatible_types():
    """Tests that if functions request an input that we correctly accept compatible types."""
    b_sig = inspect.signature(tests.resources.compatible_input_types.b)
    c_sig = inspect.signature(tests.resources.compatible_input_types.c)
    d_sig = inspect.signature(tests.resources.compatible_input_types.d)

    nodes = {
        "b": node.Node.from_fn(tests.resources.compatible_input_types.b),
        "c": node.Node.from_fn(tests.resources.compatible_input_types.c),
        "d": node.Node.from_fn(tests.resources.compatible_input_types.d),
    }
    nodes["b"]._originating_functions = (tests.resources.compatible_input_types.b,)
    nodes["c"]._originating_functions = (tests.resources.compatible_input_types.c,)
    nodes["d"]._originating_functions = (tests.resources.compatible_input_types.d,)
    # what we want to add
    param_name = "a"

    # this adds 'a' to nodes
    graph.add_dependency(
        nodes["b"],
        "b",
        nodes,
        param_name,
        b_sig.parameters[param_name].annotation,
        lifecycle_base.LifecycleAdapterSet(),
    )

    assert "a" in nodes

    # this adds 'a' to 'c' as well.
    graph.add_dependency(
        nodes["c"],
        "c",
        nodes,
        param_name,
        c_sig.parameters[param_name].annotation,
        lifecycle_base.LifecycleAdapterSet(),
    )

    # test that we shrink the type to the tighter type
    assert nodes["a"].type == str

    graph.add_dependency(
        nodes["d"],
        "d",
        nodes,
        param_name,
        d_sig.parameters[param_name].annotation,
        lifecycle_base.LifecycleAdapterSet(),
    )


def test_add_dependency_input_nodes_compatible_types_order_check():
    """Tests that if functions request an input that we correctly accept compatible types independent of order.

    This just reorders test_add_dependency_input_nodes_compatible_types to ensure the outcome does not change.
    """
    b_sig = inspect.signature(tests.resources.compatible_input_types.b)
    c_sig = inspect.signature(tests.resources.compatible_input_types.c)
    d_sig = inspect.signature(tests.resources.compatible_input_types.d)

    nodes = {
        "b": node.Node.from_fn(tests.resources.compatible_input_types.b),
        "c": node.Node.from_fn(tests.resources.compatible_input_types.c),
        "d": node.Node.from_fn(tests.resources.compatible_input_types.d),
    }
    nodes["b"]._originating_functions = (tests.resources.compatible_input_types.b,)
    nodes["c"]._originating_functions = (tests.resources.compatible_input_types.c,)
    nodes["d"]._originating_functions = (tests.resources.compatible_input_types.d,)
    # what we want to add
    param_name = "a"

    # this adds 'a' to nodes
    graph.add_dependency(
        nodes["c"],
        "c",
        nodes,
        param_name,
        c_sig.parameters[param_name].annotation,
        lifecycle_base.LifecycleAdapterSet(),
    )

    assert "a" in nodes
    assert nodes["a"].type == str

    # this adds 'a' to 'c' as well.
    graph.add_dependency(
        nodes["b"],
        "b",
        nodes,
        param_name,
        b_sig.parameters[param_name].annotation,
        lifecycle_base.LifecycleAdapterSet(),
    )

    # test that type didn't change
    assert nodes["a"].type == str

    graph.add_dependency(
        nodes["d"],
        "d",
        nodes,
        param_name,
        d_sig.parameters[param_name].annotation,
        lifecycle_base.LifecycleAdapterSet(),
    )


def test_typing_to_primitive_conversion():
    """Tests that we can mix function output being typing type, and dependent function using primitive type."""
    b_sig = inspect.signature(tests.resources.typing_vs_not_typing.B)
    func_node = node.Node(
        "B", b_sig.return_annotation, "B doc", tests.resources.typing_vs_not_typing.B
    )
    func_name = "B"
    nodes = {
        "A": node.Node(
            "A",
            inspect.signature(tests.resources.typing_vs_not_typing.A).return_annotation,
            "A doc",
            tests.resources.typing_vs_not_typing.A,
        )
    }
    param_name = "A"
    param_type = b_sig.parameters["A"].annotation

    graph.add_dependency(
        func_node,
        func_name,
        nodes,
        param_name,
        param_type,
        lifecycle_base.LifecycleAdapterSet(),
    )
    assert nodes["A"] == func_node.dependencies[0]
    assert func_node.depended_on_by == []


def test_primitive_to_typing_conversion():
    """Tests that we can mix function output being a primitive type, and dependent function using typing type."""
    b_sig = inspect.signature(tests.resources.typing_vs_not_typing.B2)
    func_node = node.Node(
        "B2", b_sig.return_annotation, "B2 doc", tests.resources.typing_vs_not_typing.B2
    )
    func_name = "B2"
    nodes = {
        "A2": node.Node(
            "A2",
            inspect.signature(tests.resources.typing_vs_not_typing.A2).return_annotation,
            "A2 doc",
            tests.resources.typing_vs_not_typing.A2,
        )
    }
    param_name = "A2"
    param_type = b_sig.parameters["A2"].annotation

    graph.add_dependency(
        func_node,
        func_name,
        nodes,
        param_name,
        param_type,
        lifecycle_base.LifecycleAdapterSet(),
    )
    assert nodes["A2"] == func_node.dependencies[0]
    assert func_node.depended_on_by == []


def test_throwing_error_on_incompatible_types():
    """Tests we error on incompatible types."""
    d_sig = inspect.signature(tests.resources.bad_functions.D)
    func_node = node.Node("D", d_sig.return_annotation, "D doc", tests.resources.bad_functions.D)
    func_name = "D"
    nodes = {
        "C": node.Node(
            "C",
            inspect.signature(tests.resources.bad_functions.C).return_annotation,
            "C doc",
            tests.resources.bad_functions.C,
        )
    }
    param_name = "C"
    param_type = d_sig.parameters["C"].annotation
    with pytest.raises(ValueError):
        graph.add_dependency(
            func_node,
            func_name,
            nodes,
            param_name,
            param_type,
            lifecycle_base.LifecycleAdapterSet(),
        )


def test_add_dependency_user_nodes():
    """Tests that we add node user defined dependencies correctly.

    Setup here is: A depends on b and c. But we're only doing one call. So expecting A having 'b' as a dependency,
    and 'b' is depended on by A.
    """
    a_sig = inspect.signature(tests.resources.dummy_functions.A)
    func_node = node.Node("A", a_sig.return_annotation, "A doc", tests.resources.dummy_functions.A)
    func_name = "A"
    nodes = {}
    param_name = "b"
    param_type = a_sig.parameters["b"].annotation

    graph.add_dependency(
        func_node,
        func_name,
        nodes,
        param_name,
        param_type,
        lifecycle_base.LifecycleAdapterSet(),
    )
    # user node is created and added to nodes.
    assert nodes["b"] == func_node.dependencies[0]
    assert nodes["b"].depended_on_by[0] == func_node
    assert func_node.depended_on_by == []


def create_testing_nodes():
    """Helper function for creating the nodes represented in dummy_functions.py."""
    nodes = {
        "A": node.Node.from_fn(fn=tests.resources.dummy_functions.A, name="A"),
        "B": node.Node.from_fn(fn=tests.resources.dummy_functions.B, name="B"),
        "C": node.Node.from_fn(fn=tests.resources.dummy_functions.C, name="C"),
        "b": node.Node(
            "b",
            inspect.signature(tests.resources.dummy_functions.A).parameters["b"].annotation,
            node_source=NodeType.EXTERNAL,
        ),
        "c": node.Node(
            "c",
            inspect.signature(tests.resources.dummy_functions.A).parameters["c"].annotation,
            node_source=NodeType.EXTERNAL,
        ),
    }
    nodes["A"].dependencies.append(nodes["b"])
    nodes["A"].dependencies.append(nodes["c"])
    nodes["A"].depended_on_by.append(nodes["B"])
    nodes["A"].depended_on_by.append(nodes["C"])
    nodes["b"].depended_on_by.append(nodes["A"])
    nodes["c"].depended_on_by.append(nodes["A"])
    nodes["B"].dependencies.append(nodes["A"])
    nodes["C"].dependencies.append(nodes["A"])
    return nodes


def create_testing_nodes_override_B():
    """Helper function for creating the nodes represented in dummy_functions.py
    with node B overridden by dummy_functions_module_override.py."""
    nodes = {
        "A": node.Node.from_fn(fn=tests.resources.dummy_functions.A, name="A"),
        "B": node.Node.from_fn(fn=tests.resources.dummy_functions_module_override.B, name="B"),
        "C": node.Node.from_fn(fn=tests.resources.dummy_functions.C, name="C"),
        "b": node.Node(
            "b",
            inspect.signature(tests.resources.dummy_functions.A).parameters["b"].annotation,
            node_source=NodeType.EXTERNAL,
        ),
        "c": node.Node(
            "c",
            inspect.signature(tests.resources.dummy_functions.A).parameters["c"].annotation,
            node_source=NodeType.EXTERNAL,
        ),
    }
    nodes["A"].dependencies.append(nodes["b"])
    nodes["A"].dependencies.append(nodes["c"])
    nodes["A"].depended_on_by.append(nodes["B"])
    nodes["A"].depended_on_by.append(nodes["C"])
    nodes["b"].depended_on_by.append(nodes["A"])
    nodes["c"].depended_on_by.append(nodes["A"])
    nodes["B"].dependencies.append(nodes["A"])
    nodes["C"].dependencies.append(nodes["A"])
    return nodes


def test_create_function_graph_simple():
    """Tests that we create a simple function graph."""
    expected = create_testing_nodes()
    actual = graph.create_function_graph(tests.resources.dummy_functions, config={})
    assert actual == expected


def test_create_function_graph_with_override():
    """Tests that we can override nodes from later modules in function graph."""
    override_expected = create_testing_nodes_override_B()
    override_actual = graph.create_function_graph(
        tests.resources.dummy_functions,
        tests.resources.dummy_functions_module_override,
        config={},
        allow_module_overrides=True,
    )
    assert override_expected == override_actual


def test_execute():
    """Tests graph execution along with basic memoization since A is depended on by two functions."""
    nodes = create_testing_nodes()
    inputs = {"b": 2, "c": 5}
    expected = {"A": 7, "B": 49, "C": 14, "b": 2, "c": 5}
    actual = graph_functions.execute_subdag(nodes=nodes.values(), inputs=inputs)
    assert actual == expected
    actual = graph_functions.execute_subdag(nodes=nodes.values(), inputs=inputs, overrides={"A": 8})
    assert actual["A"] == 8


def test_get_required_functions():
    """Exercises getting the subset of the graph for computation on the toy example we have constructed."""
    nodes = create_testing_nodes()
    final_vars = ["A", "B"]
    expected_user_nodes = {nodes["b"], nodes["c"]}
    expected_nodes = {nodes["A"], nodes["B"], nodes["b"], nodes["c"]}  # we skip 'C'
    fg = graph.FunctionGraph.from_modules(tests.resources.dummy_functions, config={})
    actual_nodes, actual_ud_nodes = fg.get_upstream_nodes(final_vars)
    assert actual_nodes == expected_nodes
    assert actual_ud_nodes == expected_user_nodes


def test_get_downstream_nodes():
    """Exercises getting the downstream subset of the graph for computation on the toy example we have constructed."""
    nodes = create_testing_nodes()
    var_changes = ["A"]
    expected_nodes = {nodes["B"], nodes["C"], nodes["A"]}
    # expected_nodes = {nodes['A'], nodes['B'], nodes['b'], nodes['c']}  # we skip 'C'
    fg = graph.FunctionGraph.from_modules(tests.resources.dummy_functions, config={})
    actual_nodes = fg.get_downstream_nodes(var_changes)
    assert actual_nodes == expected_nodes


def test_function_graph_from_multiple_sources():
    fg = graph.FunctionGraph.from_modules(
        tests.resources.dummy_functions, tests.resources.parametrized_nodes, config={}
    )
    assert len(fg.get_nodes()) == 8  # we take the union of all of them, and want to test that


def test_end_to_end_with_parametrized_nodes():
    """Tests that a simple function graph with parametrized nodes works end-to-end"""
    fg = graph.FunctionGraph.from_modules(tests.resources.parametrized_nodes, config={})
    results = fg.execute(fg.get_nodes(), {})
    assert results == {"parametrized_1": 1, "parametrized_2": 2, "parametrized_3": 3}


def test_end_to_end_with_parametrized_inputs():
    fg = graph.FunctionGraph.from_modules(
        tests.resources.parametrized_inputs, config={"static_value": 3}
    )
    results = fg.execute(fg.get_nodes())
    assert results == {
        "input_1": 1,
        "input_2": 2,
        "input_3": 3,
        "output_1": 1 + 3,
        "output_2": 2 + 3,
        "output_12": 1 + 2 + 3,
        "output_123": 1 + 2 + 3 + 3,
        "static_value": 3,
    }


def test_get_required_functions_askfor_config():
    """Tests that a simple function graph with parametrized nodes works end-to-end"""
    fg = graph.FunctionGraph.from_modules(tests.resources.parametrized_nodes, config={"a": 1})
    nodes, user_nodes = fg.get_upstream_nodes(["a", "parametrized_1"])
    (n,) = user_nodes
    assert n.name == "a"
    results = fg.execute(user_nodes)
    assert results == {"a": 1}


def test_end_to_end_with_column_extractor_nodes():
    """Tests that a simple function graph with nodes that extract columns works end-to-end"""
    fg = graph.FunctionGraph.from_modules(tests.resources.extract_column_nodes, config={})
    nodes = fg.get_nodes()
    results = fg.execute(nodes, {}, {})
    df_expected = tests.resources.extract_column_nodes.generate_df()
    pd.testing.assert_series_equal(results["col_1"], df_expected["col_1"])
    pd.testing.assert_series_equal(results["col_2"], df_expected["col_2"])
    pd.testing.assert_frame_equal(results["generate_df"], df_expected)
    assert (
        nodes[0].documentation == "Function that should be parametrized to form multiple functions"
    )


def test_end_to_end_with_multiple_decorators():
    """Tests that a simple function graph with multiple decorators on a function works end-to-end"""
    fg = graph.FunctionGraph.from_modules(
        tests.resources.multiple_decorators_together,
        config={"param0": 3, "param1": 1, "in_value1": 42, "in_value2": "string_value"},
    )
    nodes = fg.get_nodes()
    # To help debug issues:
    # nodez, user_nodes = fg.get_upstream_nodes([n.name for n in nodes],
    #                                           {"param0": 3, "param1": 1,
    #                                            "in_value1": 42, "in_value2": "string_value"})
    # fg.display(
    #     nodez,
    #     user_nodes,
    #     "all_multiple_decorators",
    #     render_kwargs=None,
    #     graphviz_kwargs=None,
    # )
    results = fg.execute(nodes, {}, {})
    df_expected = tests.resources.multiple_decorators_together._sum_multiply(3, 1, 2)
    dict_expected = tests.resources.multiple_decorators_together._sum(3, 1, 2)
    pd.testing.assert_series_equal(results["param1b"], df_expected["param1b"])
    pd.testing.assert_frame_equal(results["to_modify"], df_expected)
    assert results["total"] == dict_expected["total"]
    assert results["to_modify_2"] == dict_expected
    node_dict = {n.name: n for n in nodes}
    print(sorted(list(node_dict.keys())))
    assert (
        node_dict["to_modify"].documentation
        == "This is a dummy function showing extract_columns with does."
    )
    assert (
        node_dict["to_modify_2"].documentation
        == "This is a dummy function showing extract_fields with does."
    )
    # tag only applies right now to outer most node layer
    assert node_dict["uber_decorated_function"].tags == {
        "module": "tests.resources.multiple_decorators_together"
    }  # tags are not propagated
    assert node_dict["out_value1"].tags == {
        "module": "tests.resources.multiple_decorators_together",
        "test_key": "test-value",
    }
    assert node_dict["out_value2"].tags == {
        "module": "tests.resources.multiple_decorators_together",
        "test_key": "test-value",
    }


def test_end_to_end_with_config_modifier():
    config = {
        "fn_1_version": 1,
    }
    fg = graph.FunctionGraph.from_modules(tests.resources.config_modifier, config=config)
    results = fg.execute(fg.get_nodes(), {}, {})
    assert results["fn"] == "version_1"

    config = {
        "fn_1_version": 2,
    }
    fg = graph.FunctionGraph.from_modules(tests.resources.config_modifier, config=config)
    results = fg.execute(fg.get_nodes(), {}, {})
    assert results["fn"] == "version_2"
    config = {
        "fn_1_version": 3,
    }
    fg = graph.FunctionGraph.from_modules(tests.resources.config_modifier, config=config)
    results = fg.execute(fg.get_nodes(), {}, {})
    assert results["fn"] == "version_3"


def test_non_required_nodes():
    fg = graph.FunctionGraph.from_modules(
        tests.resources.test_default_args, config={"required": 10}
    )
    results = fg.execute(
        # D is not on the execution path, so it should not break things
        [n for n in fg.get_nodes() if n.node_role == NodeType.STANDARD and n.name != "D"],
        {},
        {},
    )
    assert results["A"] == 10
    fg = graph.FunctionGraph.from_modules(
        tests.resources.test_default_args, config={"required": 10, "defaults_to_zero": 1}
    )
    results = fg.execute(
        [n for n in fg.get_nodes() if n.node_role == NodeType.STANDARD],
        {},
        {},
    )
    assert results["A"] == 11
    assert results["D"] == 2


def test_config_can_override():
    config = {"new_param": "new_value"}
    fg = graph.FunctionGraph.from_modules(tests.resources.config_modifier, config=config)
    out = fg.execute([n for n in fg.get_nodes()])
    assert out["new_param"] == "new_value"


def test_function_graph_has_cycles_true():
    """Tests whether we catch a graph with cycles -- and expected behaviors"""
    fg = graph.FunctionGraph.from_modules(tests.resources.cyclic_functions, config={"b": 2, "c": 1})
    all_nodes = fg.get_nodes()
    nodes = [n for n in all_nodes if not n.user_defined]
    user_nodes = [n for n in all_nodes if n.user_defined]
    assert fg.has_cycles(nodes, user_nodes) is True
    required_nodes, required_user_nodes = fg.get_upstream_nodes(["A", "B", "C"])
    assert required_nodes == set(nodes + user_nodes)
    assert required_user_nodes == set(user_nodes)
    # We don't want to support this behavior officially -- but this works:
    # result = fg.execute([n for n in nodes if n.name == 'B'], overrides={'A': 1, 'D': 2})
    # assert len(result) == 3
    # assert result['B'] == 3
    with pytest.raises(
        RecursionError
    ):  # throw recursion error when we don't have a way to short circuit
        fg.execute([n for n in nodes if n.name == "B"])


def test_function_graph_has_cycles_false():
    """Tests whether we catch a graph with cycles"""
    fg = graph.FunctionGraph.from_modules(tests.resources.dummy_functions, config={"b": 1, "c": 2})
    all_nodes = fg.get_nodes()
    # checks it two ways
    nodes = [n for n in all_nodes if not n.user_defined]
    user_nodes = [n for n in all_nodes if n.user_defined]
    assert fg.has_cycles(nodes, user_nodes) is False
    # this is called by the driver
    nodes, user_nodes = fg.get_upstream_nodes(["A", "B", "C"])
    assert fg.has_cycles(nodes, user_nodes) is False


def test_function_graph_display_content(tmp_path: pathlib.Path):
    """Tests that display saves a file"""
    dot_file_path = tmp_path / "dag"
    config = {"b": 1, "c": 2}
    fg = graph.FunctionGraph.from_modules(tests.resources.dummy_functions, config=config)
    node_modifiers = {"B": {graph.VisualizationNodeModifiers.IS_OUTPUT}}
    all_nodes = set()
    for n in fg.get_nodes():
        if n.user_defined:
            node_modifiers[n.name] = {graph.VisualizationNodeModifiers.IS_USER_INPUT}
        all_nodes.add(n)
    # hack of a test -- but it works... sort the lines and match them up.
    # why? because for some reason given the same graph, the output file isn't deterministic.
    # for the same reason, order of input nodes are non-deterministic
    expected_set = set(
        [
            '\t\tfunction [fillcolor="#b4d8e4" fontname=Helvetica margin=0.15 shape=rectangle style="rounded,filled"]\n',
            '\t\tgraph [fillcolor="#ffffff" fontname=helvetica label=Legend rank=same]\n',
            '\t\tinput [fontname=Helvetica margin=0.15 shape=rectangle style="filled,dashed"]\n',
            '\t\toutput [fillcolor="#FFC857" fontname=Helvetica margin=0.15 shape=rectangle style="rounded,filled"]\n',
            "\tA -> B\n",
            "\tA -> C\n",
            '\tA [label=<<b>A</b><br /><br /><i>int</i>> fillcolor="#b4d8e4" fontname=Helvetica margin=0.15 shape=rectangle style="rounded,filled"]\n',
            '\tB [label=<<b>B</b><br /><br /><i>int</i>> fillcolor="#FFC857" fontname=Helvetica margin=0.15 shape=rectangle style="rounded,filled"]\n',
            '\tC [label=<<b>C</b><br /><br /><i>int</i>> fillcolor="#b4d8e4" fontname=Helvetica margin=0.15 shape=rectangle style="rounded,filled"]\n',
            "\tb [label=<<b>b</b><br /><br /><i>1</i>> fontname=Helvetica shape=note style=filled]\n",
            "\tc [label=<<b>c</b><br /><br /><i>2</i>> fontname=Helvetica shape=note style=filled]\n",
            "\t_A_inputs -> A\n",
            # commenting out input node: '\t_A_inputs [label=<<table border="0"><tr><td>c</td><td>int</td></tr><tr><td>b</td><td>int</td></tr></table>> fontname=Helvetica margin=0.15 shape=rectangle style=dashed]\n',
            "\tgraph [compound=true concentrate=true rankdir=LR ranksep=0.4 style=filled]\n",
            '\tnode [fillcolor="#ffffff"]\n',
            "\tsubgraph cluster__legend {\n",
            "\t}\n",
            "// Dependency Graph\n",
            "digraph {\n",
            "}\n",
        ]
    )

    fg.display(
        all_nodes,
        output_file_path=str(dot_file_path),
        node_modifiers=node_modifiers,
        config=config,
        keep_dot=True,
    )
    dot_file = dot_file_path.open("r").readlines()
    dot_set = set(dot_file)

    assert dot_set.issuperset(expected_set) and len(dot_set.difference(expected_set)) == 1


@pytest.mark.parametrize(
    "filename, keep_dot", [("dag", False), ("dag.png", False), ("dag", True), ("dag.png", True)]
)
def test_function_graph_display_output_filename(
    tmp_path: pathlib.Path, filename: str, keep_dot: bool
):
    """Handle file generation with `graph.Digraph` `.render()` and `.pipe()`"""
    output_file_path = f"{tmp_path}/{filename}"
    config = {"b": 1, "c": 2}
    fg = graph.FunctionGraph.from_modules(tests.resources.dummy_functions, config=config)

    fg.display(
        set(fg.get_nodes()),
        output_file_path=output_file_path,
        config=config,
        keep_dot=keep_dot,
    )
    assert pathlib.Path(tmp_path, "dag.png").exists()
    assert pathlib.Path(tmp_path, "dag").exists() == keep_dot


def test_function_graph_display_no_dot_output(tmp_path: pathlib.Path):
    dot_file_path = tmp_path / "dag"
    config = {"b": 1, "c": 2}
    fg = graph.FunctionGraph.from_modules(tests.resources.dummy_functions, config=config)

    fg.display(set(fg.get_nodes()), output_file_path=None, config=config)

    assert not dot_file_path.exists()


def test_function_graph_display_custom_style_node():
    def _styling_function(*, node, node_class):
        return dict(fill_color="aquamarine"), None, "legend_key"

    config = {"b": 1, "c": 2}
    fg = graph.FunctionGraph.from_modules(tests.resources.dummy_functions, config=config)

    digraph = fg.display(
        set(fg.get_nodes()),
        custom_style_function=_styling_function,
        config=config,
    )

    key_found = False
    for line in digraph.body:  # list of lines of a dot file
        if ("A" in line) and ("aquamarine" in line):
            key_found = True
            break

    assert key_found


def test_function_graph_display_custom_style_legend():
    def _styling_function(*, node, node_class):
        return dict(fill_color="aquamarine"), None, "legend_key"

    config = {"b": 1, "c": 2}
    fg = graph.FunctionGraph.from_modules(tests.resources.dummy_functions, config=config)

    digraph = fg.display(
        set(fg.get_nodes()),
        custom_style_function=_styling_function,
        config=config,
    )

    key_found = False
    for line in digraph.body:  # list of lines of a dot file
        if ("legend_key" in line) and ("aquamarine" in line):
            key_found = True
            break

    assert key_found


def test_function_graph_display_custom_style_tag():
    def _styling_function(*, node, node_class):
        if node.tags.get("some_key"):
            style = dict(fill_color="aquamarine"), None, "legend_key"
        else:
            style = dict(), None, None
        return style

    nodes = create_testing_nodes()
    nodes["A"].tags["some_key"] = "some_value"
    config = {"b": 1, "c": 2}
    fg = graph.FunctionGraph(nodes, config=config)

    digraph = fg.display(
        set(fg.get_nodes()),
        custom_style_function=_styling_function,
        config=config,
    )

    # check that style is only applied to tagged nodes
    tag_found = False
    not_tag_found = False
    for line in digraph.body:  # list of lines of a dot file
        if ("A" in line) and ("aquamarine" in line):
            tag_found = True
        elif ("B" in line) and ("aquamarine" not in line):
            not_tag_found = True

    assert tag_found and not_tag_found


@pytest.mark.parametrize("show_legend", [(True), (False)])
def test_function_graph_display_legend(show_legend: bool):
    config = {"b": 1, "c": 2}
    fg = graph.FunctionGraph.from_modules(tests.resources.dummy_functions, config=config)

    dot = fg.display(
        set(fg.get_nodes()),
        show_legend=show_legend,
        config=config,
    )

    found_legend = "cluster__legend" in dot.source
    assert found_legend is show_legend


@pytest.mark.parametrize("orient", [("LR"), ("TB"), ("RL"), ("BT")])
def test_function_graph_display_orient(orient: str):
    config = {"b": 1, "c": 2}
    fg = graph.FunctionGraph.from_modules(tests.resources.dummy_functions, config=config)

    dot = fg.display(
        set(fg.get_nodes()),
        orient=orient,
        config=config,
    )

    # this could break if a rankdir is given to the legend subgraph
    assert f"rankdir={orient}" in dot.source


@pytest.mark.parametrize("hide_inputs", [(True,), (False,)])
def test_function_graph_display_inputs(hide_inputs: bool):
    config = {"b": 1, "c": 2}
    fg = graph.FunctionGraph.from_modules(tests.resources.dummy_functions, config=config)

    dot = fg.display(
        set(fg.get_nodes()),
        hide_inputs=hide_inputs,
        config=config,
    )

    found_input = any(line.startswith("\t_") for line in dot.body)
    assert found_input is not hide_inputs


def test_function_graph_display_without_saving():
    """Tests that display works when None is passed in for path"""
    config = {"b": 1, "c": 2}
    fg = graph.FunctionGraph.from_modules(tests.resources.dummy_functions, config=config)
    all_nodes = set()
    node_modifiers = {"B": {graph.VisualizationNodeModifiers.IS_OUTPUT}}
    for n in fg.get_nodes():
        if n.user_defined:
            node_modifiers[n.name] = {graph.VisualizationNodeModifiers.IS_USER_INPUT}
        all_nodes.add(n)
    digraph = fg.display(
        all_nodes, output_file_path=None, node_modifiers=node_modifiers, config=config
    )
    assert digraph is not None
    import graphviz

    assert isinstance(digraph, graphviz.Digraph)


@pytest.mark.parametrize("display_fields", [(True,), (False,)])
def test_function_graph_display_fields(display_fields: bool):
    @schema.output(("foo", "int"), ("bar", "float"), ("baz", "str"))
    def df_with_schema() -> pd.DataFrame:
        pass

    mod = ad_hoc_utils.create_temporary_module(df_with_schema)
    config = {}
    fg = graph.FunctionGraph.from_modules(mod, config=config)

    dot = fg.display(
        set(fg.get_nodes()),
        display_fields=display_fields,
        config=config,
    )
    if display_fields:
        assert any("foo" in line for line in dot.body)
        assert any("bar" in line for line in dot.body)
        assert any("baz" in line for line in dot.body)
        assert any("cluster" in line for line in dot.body)
    else:
        assert not any("foo" in line for line in dot.body)
        assert not any("bar" in line for line in dot.body)
        assert not any("baz" in line for line in dot.body)
        assert not any("cluster" in line for line in dot.body)


def test_function_graph_display_fields_shared_schema():
    # This ensures an edge case where they end up getting dropped if there are duplicates
    SCHEMA = (("foo", "int"), ("bar", "float"), ("baz", "str"))

    @schema.output(*SCHEMA)
    def df_1_with_schema() -> pd.DataFrame:
        pass

    @schema.output(*SCHEMA)
    def df_2_with_schema() -> pd.DataFrame:
        pass

    mod = ad_hoc_utils.create_temporary_module(df_1_with_schema, df_2_with_schema)
    config = {}
    fg = graph.FunctionGraph.from_modules(mod, config=config)

    dot = fg.display(
        set(fg.get_nodes()),
        display_fields=True,
        config=config,
    )

    def _get_occurances(var: str, lines: List[str]):
        return [item for item in lines if var in item]

    # We just need to make sure these show up twice
    assert len(_get_occurances("foo=", dot.body)) == 2
    assert len(_get_occurances("bar=", dot.body)) == 2
    assert len(_get_occurances("baz=", dot.body)) == 2


def test_function_graph_display_config_node():
    """Check if config is displayed by low-level hamilton.graph.FunctionGraph.display"""
    config = {"X": 1}
    fg = graph.FunctionGraph.from_modules(tests.resources.dummy_functions, config=config)

    dot = fg.display(set(fg.get_nodes()), config=config)

    # lines start tab then node name; check if "b" is a node in the graphviz object
    assert any(line.startswith("\tX") for line in dot.body)


# TODO use high-level visualization dot as fixtures for reuse across tests
def test_display_config_node():
    """Check if config is displayed by high-level hamilton.driver.display..."""
    from hamilton import driver
    from hamilton.io.materialization import to

    config = {"X": 1}
    dr = driver.Builder().with_modules(tests.resources.dummy_functions).with_config(config).build()

    all_dot = dr.display_all_functions()
    down_dot = dr.display_downstream_of("A")
    up_dot = dr.display_upstream_of("C")
    between_dot = dr.visualize_path_between("A", "C")
    exec_dot = dr.visualize_execution(["C"], inputs={"b": 1, "c": 2})
    materialize_dot = dr.visualize_materialization(
        to.json(id="saver", dependencies=["C"], combine=base.DictResult(), path="saver.json"),
        inputs={"b": 1, "c": 2},
    )

    for dot in [all_dot, down_dot, up_dot, between_dot, exec_dot, materialize_dot]:
        assert any(line.startswith("\tX") for line in dot.body)


def test_create_graphviz_graph():
    """Tests that we create a graphviz graph"""
    config = {}
    fg = graph.FunctionGraph.from_modules(tests.resources.dummy_functions, config=config)
    nodes, user_nodes = fg.get_upstream_nodes(["A", "B", "C"])
    nodez = nodes.union(user_nodes)
    node_modifiers = {
        "b": {graph.VisualizationNodeModifiers.IS_USER_INPUT},
        "c": {graph.VisualizationNodeModifiers.IS_USER_INPUT},
        "B": {graph.VisualizationNodeModifiers.IS_OUTPUT},
    }
    # hack of a test -- but it works... sort the lines and match them up.
    # why? because for some reason given the same graph, the output file isn't deterministic.
    # for the same reason, order of input nodes are non-deterministic
    expected_set = set(
        [
            "// Dependency Graph",
            "",
            "digraph {",
            '\tnode [fillcolor="#ffffff"]',
            "\tgraph [compound=true concentrate=true rankdir=LR ranksep=0.4 ratio=1 style=filled]",
            '\tB [label=<<b>B</b><br /><br /><i>int</i>> fillcolor="#FFC857" fontname=Helvetica margin=0.15 shape=rectangle style="rounded,filled"]',
            '\tC [label=<<b>C</b><br /><br /><i>int</i>> fillcolor="#b4d8e4" fontname=Helvetica margin=0.15 shape=rectangle style="rounded,filled"]',
            '\tA [label=<<b>A</b><br /><br /><i>int</i>> fillcolor="#b4d8e4" fontname=Helvetica margin=0.15 shape=rectangle style="rounded,filled"]',
            "\tA -> B",
            "\tA -> C",
            '\t_A_inputs [label=<<table border="0"><tr><td>b</td><td>int</td></tr><tr><td>b</td><td>int</td></tr></table>> fontname=Helvetica margin=0.15 shape=rectangle style="filled,dashed"]',
            "\t_A_inputs -> A",
            "\tsubgraph cluster__legend {",
            '\t\tgraph [fillcolor="#ffffff" fontname=helvetica label=Legend rank=same]',
            '\t\tinput [fontname=Helvetica margin=0.15 shape=rectangle style="filled,dashed"]',
            '\t\tfunction [fillcolor="#b4d8e4" fontname=Helvetica margin=0.15 shape=rectangle style="rounded,filled"]',
            '\t\toutput [fillcolor="#FFC857" fontname=Helvetica margin=0.15 shape=rectangle style="rounded,filled"]',
            "\t}",
            "}",
            "",
        ]
    )

    digraph = graph.create_graphviz_graph(
        nodez,
        "Dependency Graph\n",
        graphviz_kwargs=dict(graph_attr={"ratio": "1"}),
        node_modifiers=node_modifiers,
        strictly_display_only_nodes_passed_in=False,
        config=config,
    )
    # the HTML table isn't deterministic. Replace the value in it with a single one.
    dot_set = set(str(digraph).replace("<td>c</td>", "<td>b</td>").split("\n"))
    assert dot_set == expected_set


def test_create_networkx_graph():
    """Tests that we create a networkx graph"""
    fg = graph.FunctionGraph.from_modules(tests.resources.dummy_functions, config={})
    nodes, user_nodes = fg.get_upstream_nodes(["A", "B", "C"])
    digraph = graph.create_networkx_graph(nodes, user_nodes, "test-graph")
    expected_nodes = sorted(["c", "B", "C", "b", "A"])
    expected_edges = sorted([("c", "A"), ("b", "A"), ("A", "B"), ("A", "C")])
    assert sorted(list(digraph.nodes)) == expected_nodes
    assert sorted(list(digraph.edges)) == expected_edges


def test_end_to_end_with_layered_decorators_resolves_true():
    fg = graph.FunctionGraph.from_modules(
        tests.resources.layered_decorators, config={"foo": "bar", "d": 10, "b": 20}
    )
    out = fg.execute([n for n in fg.get_nodes()])
    assert len(out) > 0  # test config.when resolves correctly
    assert out["e"] == (20 + 10)
    assert out["f"] == (20 + 20)


def test_end_to_end_with_layered_decorators_resolves_false():
    config = {"foo": "not_bar", "d": 10, "b": 20}
    fg = graph.FunctionGraph.from_modules(tests.resources.layered_decorators, config=config)
    out = fg.execute(
        [n for n in fg.get_nodes()],
    )
    assert {item: value for item, value in out.items() if item not in config} == {}


def test_combine_inputs_no_collision():
    """Tests the combine_and_validate_inputs functionality when there are no collisions"""
    combined = graph_functions.combine_config_and_inputs({"a": 1}, {"b": 2})
    assert combined == {"a": 1, "b": 2}


def test_combine_inputs_collision():
    """Tests the combine_and_validate_inputs functionality
    when there are collisions of keys but not values"""
    with pytest.raises(ValueError):
        graph_functions.combine_config_and_inputs({"a": 1}, {"a": 2})


def test_combine_inputs_collision_2():
    """Tests the combine_and_validate_inputs functionality
    when there are collisions of keys and values"""
    with pytest.raises(ValueError):
        graph_functions.combine_config_and_inputs({"a": 1}, {"a": 1})


def test_extract_columns_executes_once():
    """Ensures that extract_columns only computes the function once.
    Note this is a bit heavy-handed of a test but its nice to have."""
    fg = graph.FunctionGraph.from_modules(
        tests.resources.extract_columns_execution_count, config={}
    )
    unique_id = str(uuid.uuid4())
    fg.execute([n for n in fg.get_nodes()], inputs={"unique_id": unique_id})
    assert (
        len(tests.resources.extract_columns_execution_count.outputs[unique_id]) == 1
    )  # It should only be called once


def test_end_to_end_with_generics():
    fg = graph.FunctionGraph.from_modules(
        tests.resources.functions_with_generics, config={"b": {}, "c": 1}
    )
    results = fg.execute(fg.get_nodes())
    assert results == {
        "A": ({}, 1),
        "B": [({}, 1), ({}, 1)],
        "C": {"foo": [({}, 1), ({}, 1)]},
        "D": 1.0,
        "b": {},
        "c": 1,
    }


@pytest.mark.parametrize(
    "config,inputs,overrides",
    [
        # testing with no provided inputs
        ({}, {}, {}),
        # testing with just configs
        ({"a": 11}, {}, {}),
        ({"b": 13, "a": 17}, {}, {}),
        ({"b": 19, "a": 23, "d": 29, "f": 31}, {}, {}),
        # Testing with just inputs
        ({}, {"a": 37}, {}),
        ({}, {"b": 41, "a": 43}, {}),
        ({}, {"b": 41, "a": 43, "d": 47, "f": 53}, {}),
        # Testing with just overrides
        # TBD whether these should be legitimate -- can we override required inputs?
        # Test works now but not part of the contract
        # ({}, {}, {'a': 59}),
        # ({}, {}, {'a': 61, 'b': 67}),
        # ({}, {}, {'a': 71, 'b': 73, 'd': 79, 'f': 83}),
        # testing with a mix
        ({"a": 89}, {"b": 97}, {}),
        ({"a": 101}, {"b": 103, "d": 107}, {}),
    ],
)
def test_optional_execute(config, inputs, overrides):
    """Tests execution of optionals with different assortment of overrides, configs, inputs, etc...
    Be careful adding tests with conflicting values between them.
    """
    fg = graph.FunctionGraph.from_modules(tests.resources.optional_dependencies, config=config)
    # we put a user input node first to ensure that order does not matter with computation order.
    results = fg.execute([fg.nodes["b"], fg.nodes["g"]], inputs=inputs, overrides=overrides)
    do_all_args = {key + "_val": val for key, val in {**config, **inputs, **overrides}.items()}
    expected_results = tests.resources.optional_dependencies._do_all(**do_all_args)
    assert results["g"] == expected_results["g"]


def test_optional_input_behavior():
    """Tests that if we request optional user inputs that are not provided, we do not break. And if they are
    we do the right thing and return them.
    """
    fg = graph.FunctionGraph.from_modules(tests.resources.optional_dependencies, config={})
    # nothing passed, so nothing returned
    result = fg.execute([fg.nodes["b"], fg.nodes["a"]], inputs={}, overrides={})
    assert result == {}
    # something passed, something returned via config
    fg2 = graph.FunctionGraph.from_modules(tests.resources.optional_dependencies, config={"a": 10})
    result = fg2.execute([fg.nodes["b"], fg.nodes["a"]], inputs={}, overrides={})
    assert result == {"a": 10}
    # something passed, something returned via inputs
    result = fg.execute([fg.nodes["b"], fg.nodes["a"]], inputs={"a": 10}, overrides={})
    assert result == {"a": 10}
    # something passed, something returned via overrides
    result = fg.execute([fg.nodes["b"], fg.nodes["a"]], inputs={}, overrides={"a": 10})
    assert result == {"a": 10}


@pytest.mark.parametrize("node_order", list(permutations("fhi")))
def test_user_input_breaks_if_required_missing(node_order):
    """Tests that we break because `h` is required but is not passed in."""
    fg = graph.FunctionGraph.from_modules(tests.resources.optional_dependencies, config={})
    permutation = [fg.nodes[n] for n in node_order]
    with pytest.raises(NotImplementedError):
        fg.execute(permutation, inputs={}, overrides={})


@pytest.mark.parametrize("node_order", list(permutations("fhi")))
def test_user_input_does_not_break_if_required_provided(node_order):
    """Tests that things work no matter the order because `h` is required and is passed in, while `f` is optional."""
    fg = graph.FunctionGraph.from_modules(tests.resources.optional_dependencies, config={"h": 10})
    permutation = [fg.nodes[n] for n in node_order]
    result = fg.execute(permutation, inputs={}, overrides={})
    assert result == {"h": 10, "i": 17}


def test_optional_donot_drop_none():
    """We do not want to drop `None` results from functions. We want to pass them through to the function.

    This is here to enshrine the current behavior.
    """
    fg = graph.FunctionGraph.from_modules(tests.resources.optional_dependencies, config={"h": None})
    # enshrine behavior that None is not removed from being passed to the function.
    results = fg.execute([fg.nodes["h"], fg.nodes["i"]], inputs={}, overrides={})
    assert results == {"h": None, "i": 17}
    fg = graph.FunctionGraph.from_modules(tests.resources.optional_dependencies, config={})
    results = fg.execute(
        [fg.nodes["j"], fg.nodes["none_result"], fg.nodes["f"]], inputs={}, overrides={}
    )
    assert results == {"j": None, "none_result": None}  # f omitted cause it's optional.


def test_optional_get_required_compile_time():
    """Tests that getting required with optionals at compile time returns everything
    TODO -- change this to be testing a different function (compile time) than runtime.
    """
    fg = graph.FunctionGraph.from_modules(tests.resources.optional_dependencies, config={})
    all_upstream, user_required = fg.get_upstream_nodes(["g"])
    assert len(all_upstream) == 7  # 6 total nodes upstream
    assert len(user_required) == 4  # 4 nodes required input


def test_optional_get_required_runtime():
    fg = graph.FunctionGraph.from_modules(tests.resources.optional_dependencies, config={})
    all_upstream, user_required = fg.get_upstream_nodes(["g"], runtime_inputs={})  # Nothng required
    assert len(all_upstream) == 3  # 6 total nodes upstream
    assert len(user_required) == 0  # 4 nodes required input


def test_optional_get_required_runtime_with_provided():
    fg = graph.FunctionGraph.from_modules(tests.resources.optional_dependencies, config={})
    all_upstream, user_required = fg.get_upstream_nodes(
        ["g"], runtime_inputs={"b": 109}
    )  # Nothng required
    assert len(all_upstream) == 4  # 6 total nodes upstream
    assert len(user_required) == 1  # 4 nodes required input


def test_in_driver_function_definitions():
    """Tests that we can instantiate a DAG with a function defined in the driver, e.g. notebook context"""

    def my_function(A: int, b: int, c: int) -> int:
        """Function for input below"""
        return A + b + c

    f_module = ad_hoc_utils.create_temporary_module(my_function)
    fg = graph.FunctionGraph.from_modules(
        tests.resources.dummy_functions, f_module, config={"b": 3, "c": 1}
    )
    results = fg.execute([n for n in fg.get_nodes() if n.name in ["my_function", "A"]])
    assert results == {"A": 4, "b": 3, "c": 1, "my_function": 8}


def test_update_dependencies():
    nodes = create_testing_nodes()
    new_nodes = graph.update_dependencies(
        nodes, lifecycle_base.LifecycleAdapterSet(base.DefaultAdapter())
    )
    for node_name, node_ in new_nodes.items():
        assert node_.dependencies == nodes[node_name].dependencies
        assert node_.depended_on_by == nodes[node_name].depended_on_by
