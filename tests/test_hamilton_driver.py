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

from unittest import mock

import pandas as pd
import pytest

from hamilton import base, node, telemetry
from hamilton.caching.adapter import HamiltonCacheAdapter
from hamilton.driver import (
    Builder,
    Driver,
    InvalidExecutorException,
    TaskBasedGraphExecutor,
    Variable,
)
from hamilton.execution import executors
from hamilton.io.materialization import from_, to

import tests.resources.cyclic_functions
import tests.resources.dummy_functions
import tests.resources.dynamic_parallelism.parallel_linear_basic
import tests.resources.tagging
import tests.resources.test_default_args
import tests.resources.test_driver_serde_mapper
import tests.resources.test_driver_serde_worker
import tests.resources.test_for_materialization
import tests.resources.very_simple_dag

telemetry.MAX_COUNT_SESSION = 100

"""This file tests driver capabilities.
Anything involving execution is tested for multiple executors/driver configuration.
Anything not involving execution is tested for just the single driver configuration.

TODO -- move any execution tests to tests the graph executor capabilities on their own.
"""


@pytest.mark.parametrize(
    "driver_factory",
    [
        (lambda: Driver({"a": 1})),
        (
            lambda: Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_remote_executor(executors.SynchronousLocalTaskExecutor())
            .with_config({"a": 1})
            .build()
        ),
    ],
)
def test_driver_validate_input_types(driver_factory):
    dr = driver_factory()
    results = dr.raw_execute(["a"])
    assert results == {"a": 1}


@pytest.mark.parametrize(
    "driver_factory",
    [
        (lambda: Driver({}, tests.resources.very_simple_dag)),
        (
            lambda: Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_modules(tests.resources.very_simple_dag)
            .with_remote_executor(executors.SynchronousLocalTaskExecutor())
            .build()
        ),
    ],
)
def test_driver_validate_runtime_input_types(driver_factory):
    dr = driver_factory()
    results = dr.raw_execute(["b"], inputs={"a": 1})
    assert results == {"b": 1}


@pytest.mark.parametrize(
    "driver_factory",
    [
        (lambda: Driver({}, tests.resources.cyclic_functions)),
        (
            lambda: Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_modules(tests.resources.cyclic_functions)
            .with_remote_executor(executors.SynchronousLocalTaskExecutor())
            .build()
        ),
    ],
)
def test_driver_has_cycles_true(driver_factory):
    """Tests that we don't break when detecting cycles from the driver."""
    dr = driver_factory()
    assert dr.has_cycles(["C"])


# This is possible -- but we don't want to officially support it. Here for documentation purposes.
# def test_driver_cycles_execute_override():
#     """Tests that we short circuit a cycle by passing in overrides."""
#     dr = Driver({}, tests.resources.cyclic_functions, adapter=base.DefaultAdapter())
#     result = dr.execute(['C'], overrides={'D': 1}, inputs={'b': 2, 'c': 2})
#     assert result['C'] == 34


@pytest.mark.parametrize(
    "driver_factory",
    [
        (lambda: Driver({}, tests.resources.cyclic_functions)),
        # TODO -- fix erroring out when we try to run a driver with cycles
        # should display a better error
        # (lambda: Builder()
        #     .enable_parallelizable_type(allow_experimental_mode=True)
        #     .with_modules(tests.resources.cyclic_functions)
        #     .with_remote_executor(executors.SynchronousLocalTaskExecutor())
        #     .with_adapter(base.DefaultAdapter())
        #     .build())
    ],
)
def test_driver_cycles_execute_recursion_error(driver_factory):
    """Tests that we throw a recursion error when we try to execute over a DAG that isn't a DAG."""
    dr = driver_factory()
    with pytest.raises(RecursionError):
        dr.execute(["C"], inputs={"b": 2, "c": 2})


def test_driver_variables_exposes_tags():
    dr = Driver({}, tests.resources.tagging)
    tags = {var.name: var.tags for var in dr.list_available_variables()}
    assert tags["a"] == {"module": "tests.resources.tagging", "test": "a"}
    assert tags["b"] == {"module": "tests.resources.tagging", "test": "b_c"}
    assert tags["c"] == {"module": "tests.resources.tagging", "test": "b_c"}
    assert tags["d"] == {"module": "tests.resources.tagging", "test_list": ["us", "uk"]}


@pytest.mark.parametrize(
    "filter,expected",
    [
        (None, {"a", "b_c", "b", "c", "d"}),  # no filter
        ({}, {"a", "b_c", "b", "c", "d"}),  # empty filter
        ({"test": "b_c"}, {"b", "c"}),
        ({"test": None}, {"a", "b", "c"}),
        ({"module": "tests.resources.tagging"}, {"a", "b_c", "b", "c", "d"}),
        ({"test_list": "us"}, {"d"}),
        ({"test_list": "uk"}, {"d"}),
        ({"test_list": ["uk"]}, {"d"}),
        ({"module": "tests.resources.tagging", "test": "b_c"}, {"b", "c"}),
        ({"test_list": ["nz", "uk"]}, {"d"}),
        ({"test_list": ["us", "uk"]}, {"d"}),
        ({"test_list": ["uk", "us"]}, {"d"}),
        ({"test": ["b_c"]}, {"b", "c"}),
        ({"test": ["b_c", "foo"]}, {"b", "c"}),
    ],
    ids=[
        "filter with None passed",
        "filter with empty filter",
        "filter by single tag with extract decorator",
        "filter with None value",
        "filter with specific value",
        "filter tag with list values - value 1",
        "filter tag with list values - value 2",
        "filter tag with list values - query is single node list",
        "filter with two filter clauses",
        "filter with with list values not exact OR interpretation",
        "filter with with list values exact",
        "filter with with list values exact order invariant",
        "filter with with list values edge case one item match",
        "filter with with list values OR interpretation",
    ],
)
def test_driver_variables_filters_tags(filter, expected):
    dr = Driver({}, tests.resources.tagging)
    actual = {var.name for var in dr.list_available_variables(tag_filter=filter)}
    assert actual == expected


def test_driver_variables_filters_tags_error():
    dr = Driver({}, tests.resources.tagging)
    with pytest.raises(ValueError):
        # non string value is not allowed
        dr.list_available_variables(tag_filter={"test": 1234})
    with pytest.raises(ValueError):
        # empty list shouldn't be allowed
        dr.list_available_variables(tag_filter={"test": []})


def test_driver_variables_external_input():
    dr = Driver({}, tests.resources.very_simple_dag)
    input_types = {var.name: var.is_external_input for var in dr.list_available_variables()}
    assert input_types["a"] is True
    assert input_types["b"] is False


def test_driver_variables_exposes_original_function():
    dr = Driver({}, tests.resources.very_simple_dag)
    originating_functions = {
        var.name: var.originating_functions for var in dr.list_available_variables()
    }
    assert originating_functions["b"] == (tests.resources.very_simple_dag.b,)
    assert originating_functions["a"] == (tests.resources.very_simple_dag.b,)  # a is an input


@mock.patch("hamilton.telemetry.send_event_json")
def test_capture_constructor_telemetry_disabled(send_event_json):
    """Tests that we don't do anything if telemetry is disabled."""
    send_event_json.return_value = ""
    Driver({}, tests.resources.tagging)  # this will exercise things underneath.
    assert send_event_json.called is False


@mock.patch("hamilton.telemetry.get_adapter_name")
@mock.patch("hamilton.telemetry.send_event_json")
@mock.patch("hamilton.telemetry.g_telemetry_enabled", True)
def test_capture_constructor_telemetry_error(send_event_json, get_adapter_name):
    """Tests that we don't error if an exception occurs"""
    get_adapter_name.side_effect = ValueError("TELEMETRY ERROR")
    Driver({}, tests.resources.tagging)  # this will exercise things underneath.
    assert send_event_json.called is False


@mock.patch("hamilton.telemetry.send_event_json")
@mock.patch("hamilton.telemetry.g_telemetry_enabled", True)
def test_capture_constructor_telemetry_none_values(send_event_json):
    """Tests that we don't error if there are none values"""
    Driver({}, None, None)  # this will exercise things underneath.
    assert send_event_json.called is True


@mock.patch("hamilton.telemetry.send_event_json")
@mock.patch("hamilton.telemetry.g_telemetry_enabled", True)
def test_capture_constructor_telemetry(send_event_json):
    """Tests that we send an event if we could. Validates deterministic parts."""
    Driver({}, tests.resources.very_simple_dag)
    # assert send_event_json.called is True
    assert len(send_event_json.call_args_list) == 1  # only called once
    # check contents of what it was called with:
    send_event_json_call = send_event_json.call_args_list[0]
    actual_event_dict = send_event_json_call[0][0]
    assert actual_event_dict["api_key"] == "phc_mZg8bkn3yvMxqvZKRlMlxjekFU5DFDdcdAsijJ2EH5e"
    assert actual_event_dict["event"] == "os_hamilton_run_start"
    # validate schema
    expected_properties = {
        "$process_person_profile",
        "os_type",
        "os_version",
        "python_version",
        "distinct_id",
        "hamilton_version",
        "telemetry_version",
        "number_of_nodes",
        "number_of_modules",
        "number_of_config_items",
        "decorators_used",
        "graph_adapter_used",
        "result_builder_used",
        "driver_run_id",
        "error",
        "graph_executor_class",
        "lifecycle_adapters_used",
    }
    actual_properties = actual_event_dict["properties"]
    assert set(actual_properties.keys()) == expected_properties
    # validate static parts
    assert actual_properties["error"] is None
    assert actual_properties["number_of_nodes"] == 2  # b, and input a
    assert actual_properties["number_of_modules"] == 1
    assert actual_properties["number_of_config_items"] == 0
    assert actual_properties["number_of_config_items"] == 0
    assert actual_properties["graph_adapter_used"] == "deprecated -- see lifecycle_adapters_used"
    assert actual_properties["result_builder_used"] == "hamilton.base.PandasDataFrameResult"
    assert actual_properties["lifecycle_adapters_used"] == ["hamilton.base.PandasDataFrameResult"]


@mock.patch("hamilton.telemetry.send_event_json")
@pytest.mark.parametrize(
    "driver_factory",
    [
        (lambda: Driver({}, tests.resources.very_simple_dag)),
        (
            lambda: Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_modules(tests.resources.very_simple_dag)
            .with_adapter(base.SimplePythonGraphAdapter(base.PandasDataFrameResult()))
            .with_remote_executor(executors.SynchronousLocalTaskExecutor())
            .build()
        ),
    ],
)
def test_capture_execute_telemetry_disabled(send_event_json, driver_factory):
    """Tests that we don't do anything if telemetry is disabled."""
    dr = driver_factory()
    results = dr.execute(["b"], inputs={"a": 1})
    expected = pd.DataFrame([{"b": 1}])
    pd.testing.assert_frame_equal(results, expected)
    assert send_event_json.called is False


@mock.patch("hamilton.telemetry.send_event_json")
@mock.patch("hamilton.telemetry.g_telemetry_enabled", True)
@pytest.mark.parametrize(
    "driver_factory",
    [
        (lambda: Driver({}, tests.resources.very_simple_dag)),
        (
            lambda: Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_modules(tests.resources.very_simple_dag)
            .with_adapter(base.SimplePythonGraphAdapter(base.PandasDataFrameResult()))
            .with_remote_executor(executors.SynchronousLocalTaskExecutor())
            .build()
        ),
    ],
)
def test_capture_execute_telemetry_error(send_event_json, driver_factory):
    """Tests that we don't error if an exception occurs"""
    send_event_json.side_effect = [None, ValueError("FAKE ERROR"), None]
    dr = driver_factory()
    results = dr.execute(["b"], inputs={"a": 1})
    expected = pd.DataFrame([{"b": 1}])
    pd.testing.assert_frame_equal(results, expected)
    assert send_event_json.called is True
    assert len(send_event_json.call_args_list) == 2


@mock.patch("hamilton.telemetry.send_event_json")
@mock.patch("hamilton.telemetry.g_telemetry_enabled", True)
@pytest.mark.parametrize(
    "driver_factory",
    [
        (lambda: Driver({}, tests.resources.very_simple_dag)),
        (
            lambda: Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_modules(tests.resources.very_simple_dag)
            .with_adapter(base.SimplePythonGraphAdapter(base.PandasDataFrameResult()))
            .with_remote_executor(executors.SynchronousLocalTaskExecutor())
            .build()
        ),
    ],
)
def test_capture_execute_telemetry(send_event_json, driver_factory):
    """Happy path with values passed."""
    dr = driver_factory()
    results = dr.execute(["b"], inputs={"a": 1}, overrides={"b": 2})
    expected = pd.DataFrame([{"b": 2}])
    pd.testing.assert_frame_equal(results, expected)
    assert send_event_json.called is True
    assert len(send_event_json.call_args_list) == 2


@mock.patch("hamilton.telemetry.send_event_json")
@mock.patch("hamilton.telemetry.g_telemetry_enabled", True)
@pytest.mark.parametrize(
    "driver_factory",
    [
        (lambda: Driver({"a": 1}, tests.resources.very_simple_dag)),
        (
            lambda: Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_modules(tests.resources.very_simple_dag)
            .with_adapter(base.SimplePythonGraphAdapter(base.PandasDataFrameResult()))
            .with_remote_executor(executors.SynchronousLocalTaskExecutor())
            .with_config({"a": 1})
            .build()
        ),
    ],
)
def test_capture_execute_telemetry_none_values(send_event_json, driver_factory):
    """Happy path with none values."""
    dr = driver_factory()
    results = dr.execute(["b"])
    expected = pd.DataFrame([{"b": 1}])
    pd.testing.assert_frame_equal(results, expected)
    assert len(send_event_json.call_args_list) == 2


@pytest.mark.parametrize(
    "driver_factory",
    [
        (
            lambda: Driver(
                {"required": 1},
                tests.resources.test_default_args,
                adapter=base.DefaultAdapter(),
            )
        ),
        (
            lambda: Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_modules(tests.resources.test_default_args)
            .with_adapter(base.DefaultAdapter())
            .with_remote_executor(executors.SynchronousLocalTaskExecutor())
            .with_config({"required": 1})
            .build()
        ),
    ],
)
def test_node_is_required_by_anything(driver_factory):
    """Tests that default args are correctly interpreted.

    Specifically, if it's not in the execution path then things should
    just work. Here I'm being lazy and rather than specifically testing
    _node_is_required_by_anything() directly, I'm doing it via
    execute(), which calls it via validate_inputs().

    To understand what's going on see the functions in `test_default_args`.
    """
    dr = driver_factory()
    # D is not in the execution path, but requires defaults_to_zero
    # so this should work.
    results = dr.execute(["C"])
    assert results["C"] == 2
    with pytest.raises(ValueError):
        # D is now in the execution path, but requires defaults_to_zero
        # this should error
        dr.execute(["D"])


@pytest.mark.parametrize(
    "driver_factory",
    [
        (
            lambda: Driver(
                {"required": 1},
                tests.resources.test_default_args,
                adapter=base.DefaultAdapter(),
            )
        ),
        (
            lambda: Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_modules(tests.resources.test_default_args)
            .with_adapter(base.DefaultAdapter())
            .with_remote_executor(executors.SynchronousLocalTaskExecutor())
            .with_config({"required": 1})
            .build()
        ),
    ],
)
def test_using_callables_to_execute(driver_factory):
    """Test that you can pass a function reference and it will work fine."""
    dr = driver_factory()
    results = dr.execute(
        [tests.resources.test_default_args.C, tests.resources.test_default_args.B, "A"]
    )
    assert results["C"] == 2
    assert results["B"] == 1
    assert results["A"] == 1
    with pytest.raises(ValueError):
        dr.execute([tests.resources.cyclic_functions.B])


def test_create_final_vars():
    """Tests that the final vars are created correctly."""
    dr = Driver({"required": 1}, tests.resources.test_default_args)
    D_node = dr.graph.nodes["D"]
    actual = dr._create_final_vars(
        [
            "C",
            tests.resources.test_default_args.B,
            tests.resources.test_default_args.A,
            Variable.from_node(D_node),
        ]
    )
    expected = ["C", "B", "A", "D"]
    assert actual == expected


def test_create_final_vars_errors():
    """Tests that we catch functions pointed to in modules that aren't part of the DAG."""
    dr = Driver({"required": 1}, tests.resources.test_default_args)
    with pytest.raises(ValueError):
        dr._create_final_vars(
            ["C", tests.resources.cyclic_functions.A, tests.resources.cyclic_functions.B]
        )


def test_v2_driver_builder():
    dr = (
        Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_adapter(base.DefaultAdapter())
        .with_modules(tests.resources.very_simple_dag)
        .build()
    )
    assert isinstance(dr.graph_executor, TaskBasedGraphExecutor)
    assert list(dr.graph_modules) == [tests.resources.very_simple_dag]


def test_executor_validates_happy_default_executor():
    dr = Driver({}, tests.resources.very_simple_dag)
    nodes, user_nodes = dr.graph.get_upstream_nodes(["b"])
    dr.graph_executor.validate(nodes | user_nodes)


def test_executor_validates_sad_default_executor():
    dr = Driver({}, tests.resources.dynamic_parallelism.parallel_linear_basic)
    nodes, user_nodes = dr.graph.get_upstream_nodes(["final"])
    with pytest.raises(InvalidExecutorException):
        dr.graph_executor.validate(nodes | user_nodes)


def test_executor_validates_happy_parallel_executor():
    dr = (
        Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_modules(tests.resources.dynamic_parallelism.parallel_linear_basic)
        .build()
    )

    nodes, user_nodes = dr.graph.get_upstream_nodes(["final"])
    dr.graph_executor.validate(nodes | user_nodes)


def test_builder_defaults_to_dict_result():
    dr = Builder().with_modules(tests.resources.dummy_functions).build()

    result = dr.execute(["C"], inputs={"b": 1, "c": 1})
    assert result == {"C": 4}


def test_builder_copy():
    builder = (
        Builder()
        .with_modules(tests.resources.dummy_functions)
        .with_config({"config_key": 13})
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_adapter(base.DefaultAdapter())
        .with_local_executor(executors.SynchronousLocalTaskExecutor())
        .with_remote_executor(executors.SynchronousLocalTaskExecutor())
    )
    builder_copy = builder.copy()

    assert builder_copy is not builder
    for attr, attr_value in builder.__dict__.items():
        attr_value_copy = getattr(builder_copy, attr)
        assert attr_value_copy == attr_value
        # TODO check that each objects
        # if isinstance(attr_value, bool):
        #     continue
        # assert attr_value_copy is not attr_value


def test_builder_with_loader_materializer():
    loader_target = "external"
    loader = from_.json(target=loader_target, path="/my/file.json")
    dr = (
        Builder()
        .with_modules(tests.resources.test_for_materialization)
        .with_materializers(loader)
        .build()
    )

    assert any(n.name == f"load_data.{loader_target}" for n in dr.graph.get_nodes())


def test_builder_with_saver_materializer():
    saver_id = "saver_node"
    saver = to.json(
        id=saver_id,
        dependencies=["expects_loader"],
        path="/my/file.json",
    )
    dr = (
        Builder()
        .with_modules(tests.resources.test_for_materialization)
        .with_materializers(saver)
        .build()
    )

    assert any(n.name == saver_id for n in dr.graph.get_nodes())


def test_builder_materializer_and_execution_materializer(tmp_path):
    static_saver = to.json(
        id="static_saver",
        dependencies=["json_to_save_1"],
        path=f"{tmp_path}/file.json",
    )
    dynamic_saver = to.json(
        id="dynamic_saver",
        dependencies=["json_to_save_2"],
        path=f"{tmp_path}/file2.json",
    )
    dr = (
        Builder()
        .with_modules(tests.resources.test_for_materialization)
        .with_materializers(static_saver)
        .build()
    )
    metadata, additional = dr.materialize(dynamic_saver, additional_vars=["static_saver"])

    assert "dynamic_saver" in metadata.keys()
    assert "static_saver" in additional.keys()


def test_builder_materializer_error():
    static_saver = to.json(
        id="static_saver",
        dependencies=["json_to_save_1"],
        path="/file.json",
    )

    materializers = [static_saver]
    with pytest.raises(ValueError):
        (
            Builder()
            .with_modules(tests.resources.test_for_materialization)
            .with_materializers(materializers)
            .build()
        )

    # also check that using `*` leads to no issue
    (
        Builder()
        .with_modules(tests.resources.test_for_materialization)
        .with_materializers(*materializers)
        .build()
    )


def test_materialize_checks_required_input(tmp_path):
    dr = Builder().with_modules(tests.resources.dummy_functions).build()

    with pytest.raises(ValueError):
        dr.materialize(additional_vars=["C"], inputs={"c": 1})
    with pytest.raises(ValueError):
        dr.materialize(
            to.pickle(id="1", path=f"{tmp_path}/foo.pkl", dependencies=["C"]), inputs={"c": 1}
        )


def test_cache_raise_if_setting_twice(tmp_path):
    builder = Builder()

    builder.with_cache(path=tmp_path)
    # case 1: .with_cache() then .with_cache()
    with pytest.raises(ValueError):
        builder.with_cache(path=tmp_path)
    # case 2: .with_cache() then adding SmartCacheAdapter()
    with pytest.raises(ValueError):
        builder.with_adapters(HamiltonCacheAdapter(path=tmp_path))
    # case 3: add SmartCacheAdapter() then .with_cache()
    builder = Builder()
    builder.with_adapters(HamiltonCacheAdapter(path=tmp_path))
    with pytest.raises(ValueError):
        builder.with_cache()


def test_validate_execution_happy():
    dr = Builder().with_modules(tests.resources.very_simple_dag).build()
    dr.validate_execution(["b"], inputs={"a": 1})


def test_validate_execution_sad():
    dr = Builder().with_modules(tests.resources.very_simple_dag).build()
    with pytest.raises(ValueError):
        dr.validate_execution(["b"], inputs={})


def test_validate_materialization_happy(tmp_path):
    dr = Builder().with_modules(tests.resources.very_simple_dag).build()
    dr.validate_materialization(
        to.pickle(id="1", path=f"{tmp_path}/foo.pkl", dependencies=["b"]), inputs={"a": 1}
    )


def test_validate_materialization_sad(tmp_path):
    dr = Builder().with_modules(tests.resources.very_simple_dag).build()
    with pytest.raises(ValueError):
        dr.validate_materialization(
            # c does not exist
            # no inputs either
            to.pickle(id="1", path=f"{tmp_path}/foo.pkl", dependencies=["c"]),
            inputs={},
        )


def test_variable_from_node():
    # Quick test for creating variables from nodes --
    # this is simple but its nice to have

    def func_to_test(a: int) -> int:
        """This is a doctstring"""
        return a + 1

    n = node.Node.from_fn(func_to_test)
    v = Variable.from_node(n)
    assert v.name == n.name
    assert v.type == n.type
    assert v.tags == n.tags
    assert v.documentation == n.documentation == "This is a doctstring"
    assert v.originating_functions == n.originating_functions


def test_driver_setstate_getstate():
    """This is an integration test testing serializability of the hamilton driver."""
    from hamilton.execution import executors

    drivers = []
    inputs = []
    for i in range(4):
        dr = Builder().with_modules(tests.resources.test_driver_serde_worker).build()
        drivers.append(dr)
        inputs.append({"a": i})

    dr = (
        Builder()
        .with_modules(tests.resources.test_driver_serde_mapper)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(executors.MultiProcessingExecutor(4))
        .build()
    )
    r = dr.execute(
        final_vars=["reducer"],
        inputs={"drivers": drivers, "inputs": inputs, "final_vars": ["double"]},
    )
    assert r == {"reducer": [{"double": 0}, {"double": 2}, {"double": 4}, {"double": 6}]}
