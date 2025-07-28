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

import itertools
from typing import List

import pandas as pd
import pytest

from hamilton import ad_hoc_utils, driver
from hamilton.caching.adapter import CachingEventType, HamiltonCacheAdapter
from hamilton.caching.stores.file import FileResultStore
from hamilton.caching.stores.memory import InMemoryMetadataStore, InMemoryResultStore
from hamilton.caching.stores.sqlite import SQLiteMetadataStore
from hamilton.execution.executors import (
    MultiProcessingExecutor,
    MultiThreadingExecutor,
    SynchronousLocalTaskExecutor,
)
from hamilton.function_modifiers import cache as cache_decorator

# `metadata_store` and `result_store` are imported but not directly used because they
# are pytest fixtures automatically provided to tests
from .metadata_store.test_base import metadata_store  # noqa: F401
from .result_store.test_base import result_store  # noqa: F401
from tests.resources.dynamic_parallelism import parallel_linear_basic, parallelism_with_caching


def _instantiate_executor(executor_cls):
    if executor_cls == SynchronousLocalTaskExecutor:
        return SynchronousLocalTaskExecutor()
    elif executor_cls == MultiProcessingExecutor:
        return MultiProcessingExecutor(max_tasks=10)
    elif executor_cls == MultiThreadingExecutor:
        return MultiThreadingExecutor(max_tasks=10)
    else:
        raise ValueError(f"Class `{executor_cls}` isn't defined in `_instantiate_executor()`")


@pytest.fixture
def executor(request):
    executor_cls = request.param
    return _instantiate_executor(executor_cls)


@pytest.fixture
def dr(request, tmp_path):
    module = request.param
    return driver.Builder().with_modules(module).with_cache(path=tmp_path).build()


def execute_dataflow(
    module,
    cache,
    final_vars: list,
    config: dict = None,
    inputs: dict = None,
    overrides: dict = None,
) -> dict:
    config = config if config else {}
    inputs = inputs if inputs else {}
    overrides = overrides if overrides else {}

    dr = driver.Builder().with_modules(module).with_adapters(cache).with_config(config).build()
    results = dr.execute(final_vars, inputs=inputs, overrides=overrides)
    return results


def check_execution(cache, did: List[str] = None, did_not: List[str] = None):
    did = did if did is not None else []
    did_not = did_not if did_not is not None else []

    latest_logs = cache.logs(cache.last_run_id, level="debug")
    for did_name in did:
        assert any(e.event_type == CachingEventType.EXECUTE_NODE for e in latest_logs[did_name])

    for did_not_name in did_not:
        assert not any(
            e.event_type == CachingEventType.EXECUTE_NODE for e in latest_logs[did_not_name]
        )


def check_execution_task_based(cache, did: List[str] = None, did_not: List[str] = None):
    did = did if did is not None else []
    did_not = did_not if did_not is not None else []

    latest_logs = cache.logs(cache.last_run_id, level="debug")
    for key in latest_logs:
        if not isinstance(key, tuple):
            # keys that aren't (node_name, task_id) tuples are from the `code_version` event
            continue

        node_name, task_id = key
        if node_name in did:
            assert any(e.event_type == CachingEventType.EXECUTE_NODE for e in latest_logs[key])
        elif node_name in did_not:
            assert not any(e.event_type == CachingEventType.EXECUTE_NODE for e in latest_logs[key])


def check_metadata_store_size(cache, size: int):
    assert cache.metadata_store.size == size


def check_results_exist_in_store(cache, expected_nodes):
    run_metadata = cache.metadata_store.get_run(cache.last_run_id)

    for entry in run_metadata:
        data_version = entry["data_version"]
        if isinstance(data_version, dict):
            for item_data_version in data_version.values():
                assert cache.result_store.exists(item_data_version)
        else:
            assert cache.result_store.exists(data_version)


def node_A():
    def A() -> int:
        return 1

    return A


def node_A_code_change_same_result():
    def A() -> int:
        return 1 + 0

    return A


def node_A_code_change_different_result():
    def A() -> int:
        return 2

    return A


def node_B_depends_on_A():
    def B(A: int) -> int:
        return 0 - A

    return B


def node_B_raises():
    def B(A: int) -> int:
        raise ValueError()

    return B


def node_C_depends_on_B():
    def C(B: int) -> int:
        return B + 1

    return C


def test_code_change_same_result_do_recompute(tmp_path):
    cache = HamiltonCacheAdapter(path=tmp_path)
    module_1 = ad_hoc_utils.create_temporary_module(node_A())
    module_2 = ad_hoc_utils.create_temporary_module(node_A_code_change_same_result())
    final_vars = ["A"]

    # execution 1: populate cache
    results_1 = execute_dataflow(module=module_1, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A"])
    check_metadata_store_size(cache=cache, size=1)
    check_results_exist_in_store(cache, ["A"])

    # execution 2: retrieve under the same condition
    results_2 = execute_dataflow(module=module_1, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did_not=["A"])
    check_metadata_store_size(cache=cache, size=1)
    check_results_exist_in_store(cache, ["A"])
    assert results_2 == results_1

    # execution 3: execute after code change.
    execute_dataflow(module=module_2, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A"])


def test_code_change_different_result_do_recompute(tmp_path):
    cache = HamiltonCacheAdapter(path=tmp_path)
    module_1 = ad_hoc_utils.create_temporary_module(node_A())
    module_2 = ad_hoc_utils.create_temporary_module(node_A_code_change_different_result())
    final_vars = ["A"]

    # execution 1: populate cache
    results_1 = execute_dataflow(module=module_1, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A"])
    check_metadata_store_size(cache=cache, size=1)
    check_results_exist_in_store(cache, ["A"])

    # execution 2: retrieve under the same condition
    results_2 = execute_dataflow(module=module_1, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did_not=["A"])
    check_metadata_store_size(cache=cache, size=1)
    check_results_exist_in_store(cache, ["A"])
    assert results_2 == results_1

    # execution 3: execute after code change.
    execute_dataflow(module=module_2, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A"])


def test_input_data_change_do_recompute(tmp_path):
    cache = HamiltonCacheAdapter(path=tmp_path)
    module = ad_hoc_utils.create_temporary_module(node_B_depends_on_A())
    final_vars = ["B"]
    inputs1 = {"A": 1}
    inputs2 = {"A": 2}

    # execution 1: populate cache
    results_1 = execute_dataflow(module=module, cache=cache, final_vars=final_vars, inputs=inputs1)
    check_execution(cache=cache, did=["B"])
    check_metadata_store_size(cache=cache, size=1)
    check_results_exist_in_store(cache, ["B"])

    # execution 2: retrieve under the same condition
    results_2 = execute_dataflow(module=module, cache=cache, final_vars=final_vars, inputs=inputs1)
    check_execution(cache=cache, did_not=["B"])
    check_metadata_store_size(cache=cache, size=1)
    check_results_exist_in_store(cache, ["B"])
    assert results_2 == results_1

    # execution 3: execute with input data change
    execute_dataflow(module=module, cache=cache, final_vars=final_vars, inputs=inputs2)
    check_execution(cache=cache, did=["B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["B"])


def test_dependency_code_change_same_result_dont_recompute(tmp_path):
    cache = HamiltonCacheAdapter(path=tmp_path)
    module_1 = ad_hoc_utils.create_temporary_module(node_A(), node_B_depends_on_A())
    module_2 = ad_hoc_utils.create_temporary_module(
        node_A_code_change_same_result(), node_B_depends_on_A()
    )
    final_vars = ["B"]

    # execution 1: populate cache
    results_1 = execute_dataflow(module=module_1, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A", "B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A", "B"])

    # execution 2: retrieve under the same condition
    results_2 = execute_dataflow(module=module_1, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did_not=["A", "B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A", "B"])
    assert results_2 == results_1

    # execution 3: execute with dependency code change
    execute_dataflow(module=module_2, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A"], did_not=["B"])
    check_metadata_store_size(cache=cache, size=3)
    check_results_exist_in_store(cache, ["A", "B"])


def test_dependency_code_change_different_result_do_recompute(tmp_path):
    cache = HamiltonCacheAdapter(path=tmp_path)
    module_1 = ad_hoc_utils.create_temporary_module(node_A(), node_B_depends_on_A())
    module_2 = ad_hoc_utils.create_temporary_module(
        node_A_code_change_different_result(), node_B_depends_on_A()
    )
    final_vars = ["B"]

    # execution 1: populate cache
    results_1 = execute_dataflow(module=module_1, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A", "B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A", "B"])

    # execution 2: retrieve under the same condition
    results_2 = execute_dataflow(module=module_1, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did_not=["A", "B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A", "B"])
    assert results_2 == results_1

    # execution 3: execute with dependency code change
    execute_dataflow(module=module_2, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A", "B"])
    check_metadata_store_size(cache=cache, size=4)
    check_results_exist_in_store(cache, ["A", "B"])


def test_override_with_same_value_dont_recompute(tmp_path):
    cache = HamiltonCacheAdapter(path=tmp_path)
    module = ad_hoc_utils.create_temporary_module(node_A(), node_B_depends_on_A())
    overrides = {"A": 1}
    final_vars = ["B"]

    # execution 1: populate cache
    results_1 = execute_dataflow(module=module, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A", "B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A", "B"])

    # execution 2: retrieve under the same condition
    results_2 = execute_dataflow(module=module, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did_not=["A", "B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A", "B"])
    assert results_2 == results_1

    # execution 3: execute with override
    execute_dataflow(module=module, cache=cache, final_vars=final_vars, overrides=overrides)
    check_execution(cache=cache, did_not=["A", "B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A", "B"])


def test_override_with_different_value_do_recompute(tmp_path):
    cache = HamiltonCacheAdapter(path=tmp_path)
    module = ad_hoc_utils.create_temporary_module(node_A(), node_B_depends_on_A())
    overrides = {"A": 13}
    final_vars = ["B"]

    # execution 1: populate cache
    results_1 = execute_dataflow(module=module, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A", "B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A", "B"])

    # execution 2: retrieve under the same condition
    results_2 = execute_dataflow(module=module, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did_not=["A", "B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A", "B"])
    assert results_2 == results_1

    # execution 3: execute with override
    execute_dataflow(module=module, cache=cache, final_vars=final_vars, overrides=overrides)
    check_execution(cache=cache, did=["B"], did_not=["A"])
    check_metadata_store_size(cache=cache, size=3)
    check_results_exist_in_store(cache, ["B"])  # overrides are not stored


def test_node_that_raises_error(tmp_path):
    cache = HamiltonCacheAdapter(path=tmp_path)
    module_1 = ad_hoc_utils.create_temporary_module(node_A(), node_B_depends_on_A())
    module_2 = ad_hoc_utils.create_temporary_module(node_A(), node_B_raises())
    final_vars = ["B"]

    # execution 1: populate cache
    results_1 = execute_dataflow(module=module_1, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A", "B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A", "B"])

    # execution 2: retrieve under the same condition
    results_2 = execute_dataflow(module=module_1, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did_not=["A", "B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A", "B"])
    assert results_2 == results_1

    # execution 3: execute with raising node
    # B doesn't count as `did execute` because it raised an Exception
    with pytest.raises(ValueError):
        execute_dataflow(module=module_2, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did_not=["A"])
    assert any(
        e.event_type == CachingEventType.FAILED_EXECUTION
        for e in cache.logs(cache.run_ids[-1], level="debug")["B"]
    )
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A"])


def test_caching_pandas_dataframe(tmp_path):
    def A() -> pd.DataFrame:
        return pd.DataFrame({"foo": [0, 1], "bar": ["a", "b"]})

    def B(A: pd.DataFrame) -> pd.DataFrame:
        A["baz"] = pd.Series([True, False])
        return A

    cache = HamiltonCacheAdapter(path=tmp_path)
    module = ad_hoc_utils.create_temporary_module(A, B)
    final_vars = ["B"]

    # execution 1: populate cache
    execute_dataflow(module=module, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A", "B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A", "B"])

    # execution 2: retrieve under the same condition
    execute_dataflow(module=module, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did_not=["A", "B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A", "B"])


def test_recompute_behavior(tmp_path):
    cache = HamiltonCacheAdapter(path=tmp_path)
    module = ad_hoc_utils.create_temporary_module(node_A(), node_B_depends_on_A())
    final_vars = ["B"]

    # execution 1: populate cache
    results_1 = execute_dataflow(module=module, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A", "B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A", "B"])

    # execution 2: retrieve under the same condition
    results_2 = execute_dataflow(module=module, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did_not=["A", "B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A", "B"])
    assert results_2 == results_1

    cache._recompute = ["A"]
    # execution 3: force recompute A
    # metadata size doesn't increase because it's a duplicate entry
    execute_dataflow(module=module, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A"], did_not=["B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A", "B"])


def test_disable_behavior(tmp_path):
    cache = HamiltonCacheAdapter(path=tmp_path)
    module = ad_hoc_utils.create_temporary_module(
        node_A(), node_B_depends_on_A(), node_C_depends_on_B()
    )
    final_vars = ["C"]

    # execution 1: populate cache
    results_1 = execute_dataflow(module=module, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A", "B", "C"])
    check_metadata_store_size(cache=cache, size=3)
    check_results_exist_in_store(cache, ["A", "B", "C"])

    # execution 2: retrieve under the same condition
    results_2 = execute_dataflow(module=module, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did_not=["A", "B", "C"])
    check_metadata_store_size(cache=cache, size=3)
    check_results_exist_in_store(cache, ["A", "B", "C"])
    assert results_2 == results_1

    cache._disable = ["A"]
    # execution 3: disable A means it forces reexecution of dependent nodes
    # A doesn't produce any metadata or result
    # metadata size grows for each rexecution of B
    execute_dataflow(module=module, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A", "B"], did_not=["C"])
    check_metadata_store_size(cache=cache, size=4)
    check_results_exist_in_store(cache, ["A", "B", "C"])

    # execution 4: keeps forcing re-execution of A and B as long as A is DISABLE
    execute_dataflow(module=module, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A", "B"], did_not=["C"])
    check_metadata_store_size(cache=cache, size=5)
    check_results_exist_in_store(cache, ["A", "B", "C"])


def test_ignore_behavior(tmp_path):
    cache = HamiltonCacheAdapter(path=tmp_path)
    module = ad_hoc_utils.create_temporary_module(node_A(), node_B_depends_on_A())
    final_vars = ["B"]

    # execution 1: populate cache
    results_1 = execute_dataflow(module=module, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A", "B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A", "B"])

    # execution 2: retrieve under the same condition
    results_2 = execute_dataflow(module=module, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did_not=["A", "B"])
    check_metadata_store_size(cache=cache, size=2)
    check_results_exist_in_store(cache, ["A", "B"])
    assert results_2 == results_1

    cache._ignore = ["A"]
    # execution 3: a new key that ignores A will be recomputed for B
    # A doesn't produce any metadata or result
    execute_dataflow(module=module, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A", "B"])
    check_metadata_store_size(cache=cache, size=4)
    check_results_exist_in_store(cache, ["A", "B"])

    # execution 4: B can be retrieved using its new key that ignores A
    execute_dataflow(module=module, cache=cache, final_vars=final_vars)
    check_execution(cache=cache, did=["A"], did_not=["B"])
    check_metadata_store_size(cache=cache, size=5)
    check_results_exist_in_store(cache, ["A", "B"])


def test_result_is_materialized_to_file(tmp_path):
    @cache_decorator(format="json")
    def foo() -> dict:
        return {"hello": "world"}

    node_name = "foo"
    module = ad_hoc_utils.create_temporary_module(foo)
    dr = driver.Builder().with_modules(module).with_cache(path=tmp_path).build()

    result = dr.execute([node_name])
    data_version = dr.cache.version_data(result[node_name])
    retrieved_result = dr.cache.result_store.get(data_version)

    assert result[node_name] == retrieved_result


EXECUTORS_AND_STORES_CONFIGURATIONS = list(
    itertools.product(
        [SynchronousLocalTaskExecutor, MultiThreadingExecutor, MultiProcessingExecutor],
        [SQLiteMetadataStore],
        [FileResultStore],
    )
)

# InMemory stores can't be used with multiprocessing because they don't share memory.
IN_MEMORY_CONFIGURATIONS = list(
    itertools.product(
        [SynchronousLocalTaskExecutor, MultiThreadingExecutor],
        [InMemoryMetadataStore, SQLiteMetadataStore],
        [InMemoryResultStore, FileResultStore],
    )
)

EXECUTORS_AND_STORES_CONFIGURATIONS += IN_MEMORY_CONFIGURATIONS


@pytest.mark.parametrize(
    "executor,metadata_store,result_store", EXECUTORS_AND_STORES_CONFIGURATIONS, indirect=True
)
def test_parallel_synchronous_step_by_step(executor, metadata_store, result_store):  # noqa: F811
    dr = (
        driver.Builder()
        .with_modules(parallel_linear_basic)
        .with_cache(metadata_store=metadata_store, result_store=result_store)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(executor)
        .build()
    )

    dr.execute(["final"])
    check_execution_task_based(
        cache=dr.cache,
        did=[
            "number_of_steps",
            "steps",
            "step_squared",
            "step_cubed",
            "step_squared_plus_step_cubed",
            "sum_step_squared_plus_step_cubed",
            "final",
        ],
    )
    check_metadata_store_size(cache=dr.cache, size=22)
    check_results_exist_in_store(
        cache=dr.cache,
        expected_nodes=[
            "number_of_steps",
            "steps",
            "step_squared",
            "step_cubed",
            "step_squared_plus_step_cubed",
            "sum_step_squared_plus_step_cubed",
            "final",
        ],
    )

    # execution 2: expand node `steps` must be recomputed because of the iterator.
    dr.execute(["final"])
    check_execution_task_based(
        cache=dr.cache,
        did=["steps"],
        did_not=[
            "number_of_steps",
            "step_squared",
            "step_cubed",
            "step_squared_plus_step_cubed",
            "sum_step_squared_plus_step_cubed",
            "final",
        ],
    )
    check_metadata_store_size(cache=dr.cache, size=22)
    check_results_exist_in_store(
        cache=dr.cache,
        expected_nodes=[
            "number_of_steps",
            "steps",
            "step_squared",
            "step_cubed",
            "step_squared_plus_step_cubed",
            "sum_step_squared_plus_step_cubed",
            "final",
        ],
    )


@pytest.mark.parametrize(
    "executor",
    [SynchronousLocalTaskExecutor, MultiProcessingExecutor, MultiThreadingExecutor],
    indirect=True,
)
def test_materialize_parallel_branches(tmp_path, executor):
    # NOTE the module can't be defined here because multithreading requires functions to be top-level.
    dr = (
        driver.Builder()
        .with_modules(parallelism_with_caching)
        .with_cache(path=tmp_path)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(executor)
        .build()
    )

    # execution 1
    dr.execute(["collect_node"])
    check_execution_task_based(cache=dr.cache, did=["expand_node", "inside_branch", "collect_node"])
    check_metadata_store_size(cache=dr.cache, size=10)
    check_results_exist_in_store(
        cache=dr.cache, expected_nodes=["expand_node", "inside_branch", "collect_node"]
    )

    # execution 2: expand node must be recomputed because of the iterator.
    # values for `inside_branch` are retrieved from the JSON materialization
    dr.execute(["collect_node"])
    check_execution_task_based(
        cache=dr.cache, did=["expand_node"], did_not=["inside_branch", "collect_node"]
    )
    check_metadata_store_size(cache=dr.cache, size=10)
    check_results_exist_in_store(
        cache=dr.cache, expected_nodes=["expand_node", "inside_branch", "collect_node"]
    )


def test_consistent_cache_key_with_or_without_default_parameter(tmp_path):
    def foo(external_dep: int = 3) -> int:
        return external_dep + 1

    cache = HamiltonCacheAdapter(path=tmp_path)
    module = ad_hoc_utils.create_temporary_module(foo)
    final_vars = ["foo"]
    inputs_1 = {}
    inputs_2 = {"external_dep": 3}

    # execution 1: populate cache
    execute_dataflow(module=module, cache=cache, final_vars=final_vars, inputs=inputs_1)
    check_execution(cache=cache, did=["foo"])
    cache_key_1 = cache.cache_keys[cache.last_run_id]["foo"]

    # execution 2: retrieve under the same condition
    execute_dataflow(module=module, cache=cache, final_vars=final_vars, inputs=inputs_2)
    check_execution(cache=cache, did_not=["foo"])
    cache_key_2 = cache.cache_keys[cache.last_run_id]["foo"]

    assert cache_key_1 == cache_key_2
