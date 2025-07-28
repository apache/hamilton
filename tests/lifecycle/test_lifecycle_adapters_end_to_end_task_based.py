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

from collections import Counter
from types import ModuleType
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import pytest

from hamilton import ad_hoc_utils, driver, node
from hamilton.execution.executors import SynchronousLocalTaskExecutor
from hamilton.execution.grouping import NodeGroupPurpose
from hamilton.htypes import Collect, Parallelizable
from hamilton.lifecycle.base import (
    BaseDoNodeExecute,
    BasePostGraphConstruct,
    BasePostGraphExecute,
    BasePostNodeExecute,
    BasePostTaskExecute,
    BasePostTaskExpand,
    BasePostTaskGroup,
    BasePostTaskReturn,
    BasePreDoAnythingHook,
    BasePreGraphExecute,
    BasePreNodeExecute,
    BasePreTaskExecute,
    BasePreTaskSubmission,
)
from hamilton.node import Node

from .lifecycle_adapters_for_testing import (
    ExtendToTrackCalls,
    SentinelException,
    TrackingDoNodeExecuteHook,
    TrackingPostNodeExecuteHook,
    TrackingPostTaskExecuteHook,
    TrackingPostTaskExpandHook,
    TrackingPostTaskGroupHook,
    TrackingPostTaskReturnHook,
    TrackingPreNodeExecuteHook,
    TrackingPreTaskSubmissionHook,
)

if TYPE_CHECKING:
    from hamilton.graph import FunctionGraph


def _sample_driver(*lifecycle_adapters):
    def n_iters(n_iters_input: int) -> int:
        return n_iters_input

    def parallel_over(n_iters: int) -> Parallelizable[int]:
        for i in range(n_iters):
            yield i

    def processed(parallel_over: int) -> int:
        return parallel_over**2

    def more_processed(processed: int, broken: bool = False) -> int:
        if broken:
            raise SentinelException()
        return processed**2

    def collect(more_processed: Collect[int]) -> int:
        return sum(more_processed)

    def output(collect: int) -> int:
        return collect

    mod = ad_hoc_utils.create_temporary_module(
        n_iters, parallel_over, processed, more_processed, collect, output
    )
    return (
        driver.Builder()
        .with_modules(mod)
        .with_adapters(*lifecycle_adapters)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(SynchronousLocalTaskExecutor())
        .build()
    )


def test_individual_pre_node_execute_hook_task_based():
    hook_name = "pre_node_execute"
    hook = TrackingPreNodeExecuteHook(name=hook_name)
    dr = _sample_driver(hook)
    dr.execute(["output"], inputs={"n_iters_input": 5})
    relevant_calls = [item for item in hook.calls if item.name == hook_name]
    assert len(relevant_calls) == 14
    nodes_executed = Counter([item.bound_kwargs["node_"].name for item in relevant_calls])
    assert nodes_executed == {
        "parallel_over": 1,
        "n_iters": 1,
        "processed": 5,
        "more_processed": 5,
        "collect": 1,
        "output": 1,
    }
    run_ids = {item.bound_kwargs["run_id"] for item in relevant_calls}
    (run_id,) = run_ids
    assert len(run_ids) == 1
    assert len(run_id) > 10  # Should be UUID(ish)...


def test_individual_post_node_execute_hook_task_based():
    hook_name = "post_node_execute"
    hook = TrackingPostNodeExecuteHook(name=hook_name)
    dr = _sample_driver(hook)
    dr.execute(["output"], inputs={"n_iters_input": 5})
    relevant_calls = [item for item in hook.calls if item.name == hook_name]
    assert len(relevant_calls) == 14
    nodes_executed = Counter([item.bound_kwargs["node_"].name for item in relevant_calls])
    assert nodes_executed == {
        "parallel_over": 1,
        "n_iters": 1,
        "processed": 5,
        "more_processed": 5,
        "collect": 1,
        "output": 1,
    }
    run_ids = {item.bound_kwargs["run_id"] for item in relevant_calls}
    (run_id,) = run_ids
    assert len(run_ids) == 1
    assert len(run_id) > len(
        "TODO -- add a run ID"
    )  # This is a bit of a funny way to test that we actually added one...
    errors = {item.bound_kwargs["error"] for item in relevant_calls}
    assert len(errors) == 1  # one error, one None
    (error,) = errors
    assert error is None
    task_ids = {item.bound_kwargs["task_id"] for item in relevant_calls}
    assert (
        len(task_ids) == 2 + 5 + 1 + 1
    )  # 2 preprocessing nodes, 5 tasks, one collect, and one output node


#
def test_individual_post_node_execute_hook_task_based_with_exception():
    hook_name = "post_node_execute"
    hook = TrackingPostNodeExecuteHook(name=hook_name)
    dr = _sample_driver(hook)
    with pytest.raises(SentinelException):
        dr.execute(["output"], inputs={"n_iters_input": 1, "broken": True})
    relevant_calls = [item for item in hook.calls if item.name == hook_name]
    assert 3 < len(relevant_calls) < 9  # 3 nodes ran at least. One failed, which was counted.
    # So max is 8, if they all failed although with this implementation it will always be 4
    nodes_executed = {item.bound_kwargs["node_"].name for item in relevant_calls}
    assert nodes_executed == {"n_iters", "parallel_over", "processed", "more_processed"}
    assert {item.bound_kwargs["success"] for item in relevant_calls} == {
        True,
        False,
    }  # 2 success, 1 failure
    errors = {item.bound_kwargs["error"] for item in relevant_calls}
    assert len(errors) == 2  # one error, one None
    task_ids = {item.bound_kwargs["task_id"] for item in relevant_calls}
    assert (
        len(task_ids) >= 3
    )  # one to calc num iters, one to calc expand, and at lease one for the inner task that failed


def test_individual_post_task_execute_hook_task_based():
    hook_name = "post_task_execute"
    lifecycle_adapter = TrackingPostTaskExecuteHook(name=hook_name)
    dr = _sample_driver(lifecycle_adapter)
    dr.execute(["output"], inputs={"n_iters_input": 5})
    relevant_calls = [item for item in lifecycle_adapter.calls if item.name == hook_name]
    assert (
        len(relevant_calls) >= 2 + 5 + 1 + 1
    )  # 2 preprocessing tasks, 5 tasks, one collect, and one output node
    # Note we have >= as we actually happen to include the input, which is suboptimal, but not worth fixing now
    assert {item.bound_kwargs["success"] for item in relevant_calls} == {True}
    assert {item.bound_kwargs["error"] for item in relevant_calls} == {None}
    spawning_task_ids = Counter([item.bound_kwargs["spawning_task_id"] for item in relevant_calls])
    assert spawning_task_ids == {"expand-parallel_over": 5, None: 5}
    purposes = Counter([item.bound_kwargs["purpose"] for item in relevant_calls])
    assert purposes == {
        NodeGroupPurpose.EXECUTE_BLOCK: 5,
        NodeGroupPurpose.EXECUTE_SINGLE: 3,
        NodeGroupPurpose.EXPAND_UNORDERED: 1,
        NodeGroupPurpose.GATHER: 1,
    }


def test_individual_post_task_execute_hook_with_exception():
    hook_name = "post_task_execute"
    lifecycle_adapter = TrackingPostTaskExecuteHook(name=hook_name)
    dr = _sample_driver(lifecycle_adapter)
    with pytest.raises(SentinelException):
        dr.execute(["output"], inputs={"n_iters_input": 1, "broken": True})
    task_ids = {item.bound_kwargs["task_id"] for item in lifecycle_adapter.calls}
    assert (
        len(task_ids) >= 3
    )  # one to calc num iters, one to calc expand, and at lease one for the inner task that failed
    run_ids = {item.bound_kwargs["run_id"] for item in lifecycle_adapter.calls}
    assert len(run_ids) == 1
    success = {item.bound_kwargs["success"] for item in lifecycle_adapter.calls}
    assert len(success) == 2  # some failures, some successes
    errors = {item.bound_kwargs["error"] for item in lifecycle_adapter.calls}
    assert len(errors) == 2  # one error, one None


def test_individual_do_node_execute_method_task_based():
    method_name = "do_node_execute"
    method = TrackingDoNodeExecuteHook(name=method_name, additional_value=1)
    dr = _sample_driver(method)
    res = dr.execute(["output"], inputs={"n_iters_input": 5})
    relevant_calls = [item for item in method.calls if item.name == method_name]
    # node_names = Counter([item.bound_kwargs["node_"].name for item in relevant_calls])
    node_names = [item.bound_kwargs["node_"].name for item in relevant_calls]
    assert len(node_names) == 14
    task_ids = [item.bound_kwargs["task_id"] for item in relevant_calls]
    assert len(task_ids) >= 9
    assert (
        len(relevant_calls) == 2 + 5 * 2 + 1 + 1
    )  # 2 preprocessing nodes, 5 nodesx2 tasks, one collect, and one output node
    assert res == {"output": 426}  # Result of the above, computed but not explicitly drawn out


def test_individual_post_task_group_hook():
    hook_name = "post_task_group"
    hook = TrackingPostTaskGroupHook(name=hook_name)
    dr = _sample_driver(hook)
    dr.execute(["output"], inputs={"n_iters_input": 5})
    relevant_calls = [item for item in hook.calls if item.name == hook_name]
    assert len(relevant_calls) == 1
    task_ids = relevant_calls[0].bound_kwargs["task_ids"]
    assert len(task_ids) == 6
    assert set(task_ids) == {
        "expand-parallel_over",
        "block-parallel_over",
        "collect-parallel_over",
        "n_iters_input",
        "n_iters",
        "output",
    }
    assert len(relevant_calls[0].bound_kwargs["run_id"]) > 10  # Should be UUID(ish)...


def test_individual_post_task_expand_hook():
    hook_name = "post_task_expand"
    hook = TrackingPostTaskExpandHook(name=hook_name)
    dr = _sample_driver(hook)
    dr.execute(["output"], inputs={"n_iters_input": 5})
    relevant_calls = [item for item in hook.calls if item.name == hook_name]
    assert len(relevant_calls) == 1
    assert len(relevant_calls[0].bound_kwargs["parameters"]) == 5
    parameters = [item for item in relevant_calls[0].bound_kwargs["parameters"]]
    assert parameters == ["0", "1", "2", "3", "4"]
    assert len(relevant_calls[0].bound_kwargs["run_id"]) > 10  # Should be UUID(ish)...


def test_individual_pre_task_submission_hook():
    hook_name = "pre_task_submission"
    hook = TrackingPreTaskSubmissionHook(name=hook_name)
    dr = _sample_driver(hook)
    dr.execute(["output"], inputs={"n_iters_input": 5})
    relevant_calls = [item for item in hook.calls if item.name == hook_name]
    assert len(relevant_calls) == 10  # Total number of tasks
    spawning_task_ids = Counter([item.bound_kwargs["spawning_task_id"] for item in relevant_calls])
    assert spawning_task_ids == {"expand-parallel_over": 5, None: 5}  # Number of parallel tasks
    purposes = Counter([item.bound_kwargs["purpose"] for item in relevant_calls])
    assert purposes == {
        NodeGroupPurpose.EXPAND_UNORDERED: 1,  # Expanding task - 'parallel_over'
        NodeGroupPurpose.EXECUTE_BLOCK: 5,  # Tasks group from 'parallel_over'
        NodeGroupPurpose.GATHER: 1,  # Gathering task - 'collect'
        NodeGroupPurpose.EXECUTE_SINGLE: 3,  # All other tasks outside parallelization - single node
    }
    nodes = {node.name for item in relevant_calls for node in item.bound_kwargs["nodes"]}
    assert nodes == {
        "parallel_over",
        "n_iters",
        "processed",
        "more_processed",
        "collect",
        "output",
        "n_iters_input",
    }


def test_individual_post_task_return_hook():
    hook_name = "post_task_return"
    hook = TrackingPostTaskReturnHook(name=hook_name)
    dr = _sample_driver(hook)
    dr.execute(["output"], inputs={"n_iters_input": 5})
    relevant_calls = [item for item in hook.calls if item.name == hook_name]
    assert len(relevant_calls) == 10  # Total number of tasks
    spawning_task_ids = Counter([item.bound_kwargs["spawning_task_id"] for item in relevant_calls])
    assert spawning_task_ids == {"expand-parallel_over": 5, None: 5}  # Number of parallel tasks
    purposes = Counter([item.bound_kwargs["purpose"] for item in relevant_calls])
    assert purposes == {
        NodeGroupPurpose.EXPAND_UNORDERED: 1,  # Expanding task - 'parallel_over'
        NodeGroupPurpose.EXECUTE_BLOCK: 5,  # Tasks group from 'parallel_over'
        NodeGroupPurpose.GATHER: 1,  # Gathering task - 'collect'
        NodeGroupPurpose.EXECUTE_SINGLE: 3,  # All other tasks outside parallelization - single node
    }
    nodes = {node.name for item in relevant_calls for node in item.bound_kwargs["nodes"]}
    assert nodes == {
        "parallel_over",
        "n_iters",
        "processed",
        "more_processed",
        "collect",
        "output",
        "n_iters_input",
    }
    results = {
        item.bound_kwargs["result"]["more_processed"]
        for item in relevant_calls
        if "more_processed" in item.bound_kwargs["result"]  # only block execute results
    }
    assert results == {0, 1, 16, 81, 256}
    success = {item.bound_kwargs["success"] for item in relevant_calls}
    assert success == {True}
    errors = {item.bound_kwargs["error"] for item in relevant_calls}
    assert errors == {None}


def test_multi_hook():
    class MultiHook(
        BasePreDoAnythingHook,
        BasePostGraphConstruct,
        BasePreGraphExecute,
        BasePreTaskExecute,
        BaseDoNodeExecute,
        BasePreNodeExecute,
        BasePostNodeExecute,
        BasePostTaskExecute,
        BasePostGraphExecute,
        BasePostTaskGroup,
        BasePostTaskExpand,
        BasePreTaskSubmission,
        BasePostTaskReturn,
        ExtendToTrackCalls,
    ):
        def pre_task_execute(
            self,
            run_id: str,
            task_id: str,
            nodes: List[node.Node],
            inputs: Dict[str, Any],
            overrides: Dict[str, Any],
            spawning_task_id: Optional[str],
            purpose: NodeGroupPurpose,
        ):
            pass

        def do_node_execute(
            self,
            run_id: str,
            node_: node.Node,
            kwargs: Dict[str, Any],
            task_id: Optional[str] = None,
        ):
            return node_(**kwargs)

        def post_task_execute(
            self,
            run_id: str,
            task_id: str,
            nodes: List[node.Node],
            results: Optional[Dict[str, Any]],
            success: bool,
            error: Exception,
            spawning_task_id: Optional[str],
            purpose: NodeGroupPurpose,
        ):
            pass

        def pre_do_anything(self):
            pass

        def post_graph_construct(
            self, graph: "FunctionGraph", modules: List[ModuleType], config: Dict[str, Any]
        ):
            pass

        def pre_graph_execute(
            self,
            run_id: str,
            graph: "FunctionGraph",
            final_vars: List[str],
            inputs: Dict[str, Any],
            overrides: Dict[str, Any],
        ):
            pass

        def pre_node_execute(
            self, run_id: str, node_: Node, kwargs: Dict[str, Any], task_id: Optional[str] = None
        ):
            pass

        def post_node_execute(
            self,
            run_id: str,
            node_: node.Node,
            kwargs: Dict[str, Any],
            success: bool,
            error: Optional[Exception],
            result: Optional[Any],
            task_id: Optional[str] = None,
        ):
            pass

        def post_graph_execute(
            self,
            run_id: str,
            graph: "FunctionGraph",
            success: bool,
            error: Optional[Exception],
            results: Optional[Dict[str, Any]],
        ):
            pass

        def post_task_group(self, run_id: str, task_ids: List[str]):
            pass

        def post_task_expand(self, run_id: str, task_id: str, parameters: Dict[str, Any]):
            pass

        def pre_task_submission(
            self,
            *,
            run_id: str,
            task_id: str,
            nodes: List[Node],
            inputs: Dict[str, Any],
            overrides: Dict[str, Any],
            spawning_task_id: Optional[str],
            purpose: NodeGroupPurpose,
        ):
            pass

        def post_task_return(
            self,
            *,
            run_id: str,
            task_id: str,
            nodes: List[Node],
            result: Any,
            success: bool,
            error: Exception,
            spawning_task_id: Optional[str],
            purpose: NodeGroupPurpose,
        ):
            pass

    multi_hook = MultiHook(name="multi_hook")

    dr = _sample_driver(multi_hook)
    dr.execute(["output"], inputs={"n_iters_input": 5})
    calls = multi_hook.calls
    hook_counts = Counter([item.fn.__name__ for item in calls])
    assert hook_counts == {
        "pre_do_anything": 1,
        "post_graph_construct": 1,
        "pre_graph_execute": 1,
        "pre_task_execute": 10,
        "do_node_execute": 14,
        "pre_node_execute": 14,
        "post_node_execute": 14,
        "post_task_execute": 10,
        "post_graph_execute": 1,
        "pre_task_submission": 10,
        "post_task_return": 10,
        "post_task_group": 1,
        "post_task_expand": 1,
    }
