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

import os
import time

import numpy as np
import pytest

import hamilton.ad_hoc_utils
from hamilton import base, driver
from hamilton.execution.executors import (
    DefaultExecutionManager,
    MultiProcessingExecutor,
    MultiThreadingExecutor,
    SynchronousLocalTaskExecutor,
)
from hamilton.execution.grouping import (
    GroupByRepeatableBlocks,
    GroupNodesAllAsOne,
    GroupNodesByLevel,
    GroupNodesIndividually,
    NodeGroupPurpose,
    TaskImplementation,
)
from hamilton.htypes import Collect, Parallelizable
from hamilton.lifecycle import base as lifecycle_base

from tests.resources.dynamic_parallelism import (
    inputs_in_collect,
    no_parallel,
    parallel_collect_multiple_arguments,
    parallel_complex,
    parallel_delayed,
    parallel_linear_basic,
)

ADAPTER = base.DefaultAdapter()


def multi_processing_executor_factory():
    return MultiProcessingExecutor(max_tasks=10)


def multi_threading_executor_factory():
    return MultiThreadingExecutor(max_tasks=10)


@pytest.mark.parametrize(
    "executor_factory",
    [
        multi_processing_executor_factory,
        multi_threading_executor_factory,
        SynchronousLocalTaskExecutor,
    ],
)
def test_end_to_end_parallel_execute_group_individually(executor_factory):
    dr = (
        driver.Builder()
        .with_modules(no_parallel)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(executor_factory())
        .with_grouping_strategy(GroupNodesIndividually())
        .build()
    )
    results = dr.execute(["final"])
    assert results["final"] == no_parallel._calc()


@pytest.mark.parametrize(
    "executor_factory",
    [
        multi_processing_executor_factory,
        multi_threading_executor_factory,
        SynchronousLocalTaskExecutor,
    ],
)
def test_executors_group_all_as_one(executor_factory):
    dr = (
        driver.Builder()
        .with_modules(no_parallel)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(executor_factory())
        .with_grouping_strategy(GroupNodesAllAsOne())
        .build()
    )

    results = dr.execute(["final"])
    assert results["final"] == no_parallel._calc()


@pytest.mark.parametrize(
    "executor_factory",
    [
        multi_processing_executor_factory,
        multi_threading_executor_factory,
        SynchronousLocalTaskExecutor,
    ],
)
def test_executors_group_by_level(executor_factory):
    dr = (
        driver.Builder()
        .with_modules(no_parallel)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(executor_factory())
        .with_grouping_strategy(GroupNodesByLevel())
        .build()
    )
    result = dr.execute(["final"])
    assert result["final"] == no_parallel._calc()


@pytest.mark.parametrize(
    "executor_factory",
    [
        multi_processing_executor_factory,
        multi_threading_executor_factory,
        SynchronousLocalTaskExecutor,
    ],
)
def test_end_to_end_parallel_execute_group_by_repeatable_blocks(executor_factory):
    dr = (
        driver.Builder()
        .with_modules(parallel_linear_basic)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(executor_factory())
        .with_grouping_strategy(GroupByRepeatableBlocks())
        .build()
    )
    result = dr.execute(["final"])
    assert result["final"] == parallel_linear_basic._calc()


@pytest.mark.parametrize(
    "executor_factory", [multi_processing_executor_factory, multi_threading_executor_factory]
)
def test_parallelism_would_take_too_long_with_no_parallelism(executor_factory):
    dr = (
        driver.Builder()
        .with_modules(parallel_delayed)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(executor_factory())
        .with_grouping_strategy(GroupByRepeatableBlocks())
        .build()
    )
    t0 = time.time()
    delay_seconds = 1.0
    number_of_steps = 30
    result = dr.execute(
        ["final"], inputs={"delay_seconds": delay_seconds, "number_of_steps": number_of_steps}
    )
    t1 = time.time()
    assert result["final"] == 197780
    time_taken = t1 - t0
    assert time_taken < 10


@pytest.mark.parametrize(
    "executor_factory",
    [
        multi_processing_executor_factory,
        multi_threading_executor_factory,
        SynchronousLocalTaskExecutor,
    ],
)
def test_end_to_end_block_has_external_dependencies(executor_factory):
    dr = (
        driver.Builder()
        .with_modules(parallel_complex)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(executor_factory())
        .with_grouping_strategy(GroupByRepeatableBlocks())
        .build()
    )
    result = dr.execute(["final"])
    assert result["final"] == 165


@pytest.mark.parametrize(
    "executor_factory",
    [
        multi_processing_executor_factory,
        multi_threading_executor_factory,
        SynchronousLocalTaskExecutor,
    ],
)
def test_end_to_end_with_overrides(executor_factory):
    dr = (
        driver.Builder()
        .with_modules(parallel_complex)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(executor_factory())
        .with_grouping_strategy(GroupByRepeatableBlocks())
        .build()
    )
    result = dr.execute(
        ["final"],
        overrides={
            "number_of_steps": 2,
            "param_external_to_block": 0,
            "second_param_external_to_block": 0,
        },
    )
    assert result["final"] == 5


def create_dummy_task(task_purpose: NodeGroupPurpose):
    return TaskImplementation(
        base_id="foo",
        spawning_task_base_id="foo",
        nodes=[],
        purpose=task_purpose,
        outputs_to_compute=[],
        overrides={},
        adapter=lifecycle_base.LifecycleAdapterSet(),
        base_dependencies=[],
        group_id=None,
        realized_dependencies={},
        spawning_task_id=None,
        dynamic_inputs={},
        run_id="foo",
    )


@pytest.mark.parametrize(
    "purpose, check",
    [
        (NodeGroupPurpose.EXECUTE_BLOCK, lambda x: isinstance(x, MultiProcessingExecutor)),
        (NodeGroupPurpose.EXECUTE_SINGLE, lambda x: isinstance(x, SynchronousLocalTaskExecutor)),
        (NodeGroupPurpose.EXPAND_UNORDERED, lambda x: isinstance(x, SynchronousLocalTaskExecutor)),
        (NodeGroupPurpose.GATHER, lambda x: isinstance(x, SynchronousLocalTaskExecutor)),
    ],
)
def test_get_execotor_for_tasks_default_execution_manager(purpose, check):
    execution_manager = DefaultExecutionManager(
        local_executor=SynchronousLocalTaskExecutor(),
        remote_executor=MultiProcessingExecutor(max_tasks=10),
    )
    assert check(execution_manager.get_executor_for_task(create_dummy_task(purpose)))


def test_end_to_end_parallelizable_with_input_in_collect():
    dr = (
        driver.Builder()
        .with_modules(inputs_in_collect)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(SynchronousLocalTaskExecutor())
    ).build()
    assert dr.execute(["collect"])["collect"] == 46


def test_end_to_end_parallelizable_with_overrides_on_expand_node():
    dr = (
        driver.Builder()
        .with_modules(inputs_in_collect)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(SynchronousLocalTaskExecutor())
    ).build()
    assert dr.execute(["collect"], overrides={"par": [1, 2, 3]})["collect"] == 7


def test_end_to_end_parallelizable_with_overrides_on_collect_node():
    dr = (
        driver.Builder()
        .with_modules(inputs_in_collect)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(SynchronousLocalTaskExecutor())
    ).build()
    assert dr.execute(["collect_plus_one"], overrides={"collect": 100})["collect_plus_one"] == 101


@pytest.mark.skipif(
    os.environ.get("CI") != "true",
    reason="This test tests memory usage and takes quite a while to run."
    "We don't run it locally as its a low-touch part of the codebase"
    "TODO -- actually measure the memory allocated/remaining",
)
def test_sequential_would_use_too_much_memory_no_garbage_collector():
    NUM_REPS = 1000

    def foo() -> Parallelizable[int]:
        for i in range(NUM_REPS):
            yield i

    def large_allocation(foo: int) -> np.array:
        size = int(1_073_741_824 / 10)  # 1 GB in bytes
        return np.ones(size)

    def compressed(large_allocation: np.array) -> int:
        import gc

        gc.collect()
        return 1

    # This is a hack due to python's garbage collector
    def gc(compressed: int) -> int:
        return compressed

    def concatenated(gc: Collect[int]) -> int:
        return sum(gc)

    mod = hamilton.ad_hoc_utils.create_temporary_module(
        foo, large_allocation, compressed, gc, concatenated
    )

    dr = (
        driver.Builder()
        .with_modules(mod)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(SynchronousLocalTaskExecutor())
        .with_grouping_strategy(GroupByRepeatableBlocks())
        .build()
    )
    result = dr.execute(["concatenated"])
    assert result["concatenated"] == NUM_REPS


def test_parallel_end_to_end_with_collect_multiple_inputs():
    dr = (
        driver.Builder()
        .with_modules(parallel_collect_multiple_arguments)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(SynchronousLocalTaskExecutor())
        .with_grouping_strategy(GroupByRepeatableBlocks())
        .build()
    )
    parallel_collect_multiple_arguments._reset_counter()
    ITERS = 100
    res = dr.execute(["summed"], inputs={"iterations": ITERS})
    assert res["summed"] == ((ITERS**2 - ITERS) / 2) * 2 - 2 - 1
    counts = parallel_collect_multiple_arguments._fn_call_counter
    assert counts == {
        "not_to_repeat": 1,
        "number_to_repeat": 1,
        "something_else_not_to_repeat": 1,
        "double": ITERS,
        "summed": 1,
    }


def test_parallel_end_to_end_with_empty_list():
    dr = (
        driver.Builder()
        .with_modules(parallel_linear_basic)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(SynchronousLocalTaskExecutor())
        .with_adapter(base.DefaultAdapter())
        .build()
    )
    parallel_collect_multiple_arguments._reset_counter()
    res = dr.execute(["final"], overrides={"number_of_steps": 0})
    assert res["final"] == parallel_linear_basic._calc(0)
