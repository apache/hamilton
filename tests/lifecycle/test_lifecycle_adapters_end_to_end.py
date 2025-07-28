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

from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

import pytest

from hamilton import ad_hoc_utils, driver, node
from hamilton.io.materialization import to
from hamilton.lifecycle.base import (
    BaseDoNodeExecute,
    BaseDoRemoteExecute,
    BasePostGraphConstruct,
    BasePostGraphExecute,
    BasePostNodeExecute,
    BasePreDoAnythingHook,
    BasePreGraphExecute,
    BasePreNodeExecute,
    ValidationException,
)
from hamilton.node import Node

from .lifecycle_adapters_for_testing import (
    ExtendToTrackCalls,
    SentinelException,
    TrackingDoBuildResultMethod,
    TrackingDoNodeExecuteHook,
    TrackingDoRemoteExecuteHook,
    TrackingDoValidateInputMethod,
    TrackingPostGraphConstructHook,
    TrackingPostGraphExecuteHook,
    TrackingPostNodeExecuteHook,
    TrackingPreDoAnythingHook,
    TrackingPreGraphExecuteHook,
    TrackingPreNodeExecuteHook,
    TrackingValidateGraphValidator,
    TrackingValidateNodeValidator,
)

if TYPE_CHECKING:
    from hamilton.graph import FunctionGraph


def _sample_driver(*lifecycle_adapters):
    def a(input: int) -> int:
        return int(input) % 7  # Cause we're messing with the inputs for a lifecycle method

    def b(a: int) -> int:
        return a * 2

    def c(a: int, b: int, broken: bool = False) -> int:
        if broken:
            raise SentinelException("broken")
        return a * 3 + b * 2

    def d(c: int) -> int:
        return c**3

    mod = ad_hoc_utils.create_temporary_module(a, b, c, d)
    return driver.Builder().with_modules(mod).with_adapters(*lifecycle_adapters).build()


def test_individual_pre_do_anything_hook():
    hook_name = "pre_do_anything"
    hook = TrackingPreDoAnythingHook(name=hook_name)
    dr = _sample_driver(hook)
    dr.execute(["d"], inputs={"input": 1})
    relevant_calls = [item for item in hook.calls if item.name == hook_name]
    assert len(relevant_calls) == 1
    (adapter_call,) = relevant_calls
    assert adapter_call.bound_kwargs == {}


def test_individual_post_graph_construct_hook():
    hook_name = "post_graph_construct"
    hook = TrackingPostGraphConstructHook(name=hook_name)
    dr = _sample_driver(hook)
    dr.execute(["d"], inputs={"input": 1})
    relevant_calls = [item for item in hook.calls if item.name == hook_name]
    assert len(relevant_calls) == 1
    (adapter_call,) = relevant_calls
    assert adapter_call.fn.__name__ == hook.post_graph_construct.__name__
    assert "graph" in adapter_call.bound_kwargs
    assert "modules" in adapter_call.bound_kwargs
    assert "config" in adapter_call.bound_kwargs


def test_individual_pre_graph_execute_hook():
    hook_name = "pre_graph_execute"
    hook = TrackingPreGraphExecuteHook(name=hook_name)
    dr = _sample_driver(hook)
    dr.execute(["d"], inputs={"input": 1})
    relevant_calls = [item for item in hook.calls if item.name == hook_name]
    assert len(relevant_calls) == 1
    (adapter_call,) = relevant_calls
    assert adapter_call.fn.__name__ == "pre_graph_execute"
    assert "run_id" in adapter_call.bound_kwargs
    run_ids = {item.bound_kwargs["run_id"] for item in relevant_calls}
    assert len(run_ids) == 1
    (run_id,) = run_ids
    assert run_id is not None
    assert len(run_id) > 10  # Just a sanity check
    assert "graph" in adapter_call.bound_kwargs
    assert "final_vars" in adapter_call.bound_kwargs
    assert "inputs" in adapter_call.bound_kwargs
    assert "overrides" in adapter_call.bound_kwargs


def test_individual_pre_node_execute_hook():
    hook_name = "pre_node_execute"
    hook = TrackingPreNodeExecuteHook(name=hook_name)
    dr = _sample_driver(hook)
    dr.execute(["d"], inputs={"input": 1})
    relevant_calls = [item for item in hook.calls if item.name == hook_name]
    assert len(relevant_calls) == 4  # 4 nodes
    nodes_executed = {item.bound_kwargs["node_"].name for item in relevant_calls}
    assert nodes_executed == {"a", "b", "c", "d"}
    run_ids = {item.bound_kwargs["run_id"] for item in relevant_calls}
    assert len(run_ids) == 1
    (run_id,) = run_ids
    assert run_id is not None
    assert len(run_id) > 10  # Just a sanity check
    task_ids = {item.bound_kwargs["task_id"] for item in relevant_calls}
    assert len(task_ids) == 1
    (task_id,) = task_ids
    assert task_id is None


def test_individual_post_node_execute_hook():
    hook_name = "post_node_execute"
    hook = TrackingPostNodeExecuteHook(name=hook_name)
    dr = _sample_driver(hook)
    dr.execute(["d"], inputs={"input": 1})
    relevant_calls = [item for item in hook.calls if item.name == hook_name]
    assert len(relevant_calls) == 4  # 4 nodes
    nodes_executed = {item.bound_kwargs["node_"].name for item in relevant_calls}
    assert nodes_executed == {"a", "b", "c", "d"}
    assert {item.bound_kwargs["success"] for item in relevant_calls} == {True}
    assert {item.bound_kwargs["error"] for item in relevant_calls} == {None}
    task_ids = {item.bound_kwargs["task_id"] for item in relevant_calls}
    assert len(task_ids) == 1
    (task_id,) = task_ids
    assert task_id is None
    run_ids = {item.bound_kwargs["run_id"] for item in relevant_calls}
    assert len(run_ids) == 1
    (run_id,) = run_ids
    assert run_id is not None
    assert len(run_id) > 10  # Just a sanity check


def test_individual_post_node_execute_hook_with_exception():
    hook_name = "post_node_execute"
    hook = TrackingPostNodeExecuteHook(name=hook_name)
    dr = _sample_driver(hook)
    with pytest.raises(SentinelException):
        dr.execute(["d"], inputs={"input": 1, "broken": True})
    relevant_calls = [item for item in hook.calls if item.name == hook_name]
    assert len(relevant_calls) == 3  # 3 nodes ran, one failed
    nodes_executed = {item.bound_kwargs["node_"].name for item in relevant_calls}
    assert nodes_executed == {"a", "b", "c"}
    assert {item.bound_kwargs["success"] for item in relevant_calls} == {
        True,
        False,
    }  # 2 success, 1 failure
    errors = {item.bound_kwargs["error"] for item in relevant_calls}
    assert len(errors) == 2  # one error, one None
    task_ids = {item.bound_kwargs["task_id"] for item in relevant_calls}
    assert len(task_ids) == 1
    (task_id,) = task_ids
    assert task_id is None
    run_ids = {item.bound_kwargs["run_id"] for item in relevant_calls}
    assert len(run_ids) == 1
    (run_id,) = run_ids
    assert run_id is not None
    assert len(run_id) > 10  # Just a sanity check


def test_individual_post_graph_execute_hook():
    hook_name = "post_graph_execute"
    hook = TrackingPostGraphExecuteHook(name=hook_name)
    dr = _sample_driver(hook)
    dr.execute(["d"], inputs={"input": 1})
    relevant_calls = [item for item in hook.calls if item.name == hook_name]
    assert len(relevant_calls) == 1  # 1 task
    (adapter_call,) = relevant_calls
    assert adapter_call.fn.__name__ == "post_graph_execute"
    assert "run_id" in adapter_call.bound_kwargs
    assert "graph" in adapter_call.bound_kwargs
    assert adapter_call.bound_kwargs["success"] is True
    assert adapter_call.bound_kwargs["error"] is None
    assert adapter_call.bound_kwargs["results"] is not None
    run_ids = {item.bound_kwargs["run_id"] for item in relevant_calls}
    assert len(run_ids) == 1
    (run_id,) = run_ids
    assert run_id is not None
    assert len(run_id) > 10  # Just a sanity check


def test_individual_post_graph_execute_hook_with_exception():
    hook_name = "post_graph_execute"
    hook = TrackingPostGraphExecuteHook(name=hook_name)
    dr = _sample_driver(hook)
    with pytest.raises(SentinelException):
        dr.execute(["d"], inputs={"input": 1, "broken": True})
    relevant_calls = [item for item in hook.calls if item.name == hook_name]
    assert len(relevant_calls) == 1  # 1 task
    (adapter_call,) = relevant_calls
    assert adapter_call.fn.__name__ == "post_graph_execute"
    assert adapter_call.bound_kwargs["success"] is False
    assert isinstance(adapter_call.bound_kwargs["error"], SentinelException)
    assert adapter_call.bound_kwargs["results"] is None
    run_ids = {item.bound_kwargs["run_id"] for item in relevant_calls}
    assert len(run_ids) == 1
    (run_id,) = run_ids
    assert run_id is not None
    assert len(run_id) > 10  # Just a sanity check


def test_multiple_hooks():
    """Tests that all hooks are passed in"""
    all_hooks = [
        TrackingPreDoAnythingHook(name="pre_do_anything"),
        TrackingPostGraphConstructHook(name="post_graph_construct"),
        TrackingPreGraphExecuteHook(name="pre_graph_execute"),
        TrackingPreNodeExecuteHook(name="pre_node_execute"),
        TrackingPostNodeExecuteHook(name="post_node_execute"),
        TrackingPostGraphExecuteHook(name="post_graph_execute"),
    ]
    dr = _sample_driver(*all_hooks)
    dr.execute(["d"], inputs={"input": 1})
    # We want to make sure that the order of calls is correct
    calls_by_name = dict((hook.name, hook.calls) for hook in all_hooks)
    sequence_number_current = -1
    for hook_name in [
        "pre_do_anything",
        "post_graph_construct",
        "pre_graph_execute",
        "post_graph_execute",
    ]:
        assert len(calls_by_name[hook_name]) == 1
        (call,) = calls_by_name[hook_name]
        assert call.sequence_number > sequence_number_current
        sequence_number_current = call.sequence_number

    for hook_name in ["pre_node_execute", "post_node_execute"]:
        assert len(calls_by_name[hook_name]) == 4


def test_multiple_hooks_with_execution_exception():
    all_hooks = [
        TrackingPreDoAnythingHook(name="pre_do_anything"),
        TrackingPostGraphConstructHook(name="post_graph_construct"),
        TrackingPreGraphExecuteHook(name="pre_graph_execute"),
        TrackingPreNodeExecuteHook(name="pre_node_execute"),
        TrackingPostNodeExecuteHook(name="post_node_execute"),
        TrackingPostGraphExecuteHook(name="post_graph_execute"),
    ]
    dr = _sample_driver(*all_hooks)
    with pytest.raises(SentinelException):
        dr.execute(["d"], inputs={"input": 1, "broken": True})
    calls_by_name = dict((hook.name, hook.calls) for hook in all_hooks)
    sequence_number_current = -1
    for hook_name in [
        "pre_do_anything",
        "post_graph_construct",
        "pre_graph_execute",
        "post_graph_execute",
    ]:
        assert len(calls_by_name[hook_name]) == 1
        (call,) = calls_by_name[hook_name]
        assert call.sequence_number > sequence_number_current
        sequence_number_current = call.sequence_number
    for hook_name in ["pre_node_execute", "post_node_execute"]:
        assert len(calls_by_name[hook_name]) == 3  # Each is executed 3 times


def test_multi_hook():
    class MultiHook(
        BasePreDoAnythingHook,
        BasePostGraphConstruct,
        BasePreGraphExecute,
        BasePreNodeExecute,
        BaseDoNodeExecute,
        BasePostNodeExecute,
        BasePostGraphExecute,
        ExtendToTrackCalls,
    ):
        def do_node_execute(
            self,
            run_id: str,
            node_: node.Node,
            kwargs: Dict[str, Any],
            task_id: Optional[str] = None,
        ):
            return node_(**kwargs)

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

    multi_hook = MultiHook(name="multi_hook")

    dr = _sample_driver(multi_hook)
    dr.execute(["d"], inputs={"input": 1})
    calls = multi_hook.calls
    assert len(calls) == 16


def test_multi_hook_remote():
    class MultiHook(
        BasePreDoAnythingHook,
        BasePostGraphConstruct,
        BasePreGraphExecute,
        BasePreNodeExecute,
        BaseDoRemoteExecute,
        BasePostNodeExecute,
        BasePostGraphExecute,
        ExtendToTrackCalls,
    ):
        def do_remote_execute(
            self,
            node: node.Node,
            execute_lifecycle_for_node: Callable,
            **kwargs: Dict[str, Any],
        ):
            return execute_lifecycle_for_node(**kwargs)

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

    multi_hook = MultiHook(name="multi_hook")

    dr = _sample_driver(multi_hook)
    dr.execute(["d"], inputs={"input": 1})
    calls = multi_hook.calls
    assert len(calls) == 16


def test_individual_do_validate_input_method():
    method_name = "do_validate_input"
    method = TrackingDoValidateInputMethod(name=method_name, valid=True)
    dr = _sample_driver(method)
    dr.execute(["d"], inputs={"input": "1"})  # this is allowed by the method
    relevant_calls = [item for item in method.calls if item.name == method_name]
    (adapter_call,) = relevant_calls
    assert adapter_call.fn.__name__ == "do_validate_input"
    assert adapter_call.bound_kwargs["input_value"] == "1"
    assert adapter_call.result is True


def test_individual_do_validate_input_method_invalid():
    method_name = "do_validate_input"
    method = TrackingDoValidateInputMethod(name=method_name, valid=False)
    dr = _sample_driver(method)
    with pytest.raises(ValueError):
        dr.execute(["d"], inputs={"input": "1"})
    relevant_calls = [item for item in method.calls if item.name == method_name]
    (adapter_call,) = relevant_calls
    assert adapter_call.fn.__name__ == "do_validate_input"
    assert adapter_call.bound_kwargs["input_value"] == "1"
    assert adapter_call.result is False


def test_individual_do_node_execute_method():
    method_name = "do_node_execute"
    method = TrackingDoNodeExecuteHook(name=method_name, additional_value=1)
    dr = _sample_driver(method)
    res = dr.execute(["d"], inputs={"input": 1})
    relevant_calls = [item for item in method.calls if item.name == method_name]
    assert len(relevant_calls) == 4
    assert res == {"d": 17**3 + 1}  # adding one to each one


def test_individual_do_remote_execute_method():
    method_name = "do_remote_execute"
    method = TrackingDoRemoteExecuteHook(name=method_name, additional_value=1)
    dr = _sample_driver(method)
    res = dr.execute(["d"], inputs={"input": 1})
    relevant_calls = [item for item in method.calls if item.name == method_name]
    assert len(relevant_calls) == 4
    assert res == {"d": 17**3 + 1}  # adding one to each one


def test_individual_do_build_results_method():
    method_name = "do_build_result"
    method = TrackingDoBuildResultMethod(name=method_name, result=-1)
    dr = _sample_driver(method)
    res = dr.execute(["d"], inputs={"input": 1})
    relevant_calls = [item for item in method.calls if item.name == method_name]
    assert len(relevant_calls) == 1
    (adapter_call,) = relevant_calls
    assert res == -1
    assert adapter_call.bound_kwargs == {"outputs": {"d": 7**3}}


def test_multiple_hooks_materialize():
    # Just a single test as the codepaths are largely the same
    all_hooks = [
        TrackingPreDoAnythingHook(name="pre_do_anything"),
        TrackingPostGraphConstructHook(name="post_graph_construct"),
        TrackingPreGraphExecuteHook(name="pre_graph_execute"),
        TrackingPreNodeExecuteHook(name="pre_node_execute"),
        TrackingPostNodeExecuteHook(name="post_node_execute"),
        TrackingPostGraphExecuteHook(name="post_graph_execute"),
    ]
    dr = _sample_driver(*all_hooks)
    with pytest.raises(SentinelException):
        dr.materialize(to.memory(id="...", dependencies=["d"]), inputs={"input": 1, "broken": True})
    calls_by_name = dict((hook.name, hook.calls) for hook in all_hooks)
    sequence_number_current = -1
    for hook_name in [
        "pre_do_anything",
        "pre_graph_execute",
        "post_graph_execute",
    ]:
        assert len(calls_by_name[hook_name]) == 1
        (call,) = calls_by_name[hook_name]
        assert call.sequence_number > sequence_number_current
        sequence_number_current = call.sequence_number
    # This is called twice -- once when the graph is contructed in
    assert len(calls_by_name["post_graph_construct"]) == 2
    for hook_name in ["pre_node_execute", "post_node_execute"]:
        assert len(calls_by_name[hook_name]) == 3  # Each is executed 3 times


def test_individual_validate_node_validator_valid():
    validator_name = "validate_node"
    validator = TrackingValidateNodeValidator(name=validator_name, valid=True, message=None)
    _sample_driver(validator)  # Instantiating it just works
    relevant_calls = [item for item in validator.calls if item.name == validator_name]
    # TODO -- consider if we want to limit it to just the user-facing nodes
    assert len(relevant_calls) == 6  # one for each node then one for both inputs...


def test_individual_validate_node_validator_invalid():
    validator_name = "validate_node"
    validator = TrackingValidateNodeValidator(
        name=validator_name, valid=False, message="test message"
    )
    with pytest.raises(ValidationException):  # it groups and then gets called from that
        _sample_driver(validator)  # These are raised on instantiation
    relevant_calls = [item for item in validator.calls if item.name == validator_name]
    assert (
        len(relevant_calls) == 6
    )  # one for each node, we call everything and error out at the end
    assert all(item.result[0] is False for item in relevant_calls)


def test_individual_graph_validator_valid():
    validator_name = "validate_graph"
    validator = TrackingValidateGraphValidator(name=validator_name, valid=True, message=None)
    _sample_driver(validator)  # Instantiating it just works
    relevant_calls = [item for item in validator.calls if item.name == validator_name]
    assert len(relevant_calls) == 1


def test_individual_graph_validator_invalid():
    validator_name = "validate_graph"
    validator = TrackingValidateGraphValidator(
        name=validator_name, valid=False, message="test message"
    )
    with pytest.raises(ValidationException):  # it groups and then gets called from that
        _sample_driver(validator)  # These are raised on instantiation
    relevant_calls = [item for item in validator.calls if item.name == validator_name]
    assert (
        len(relevant_calls) == 1
    )  # one for each node, we call everything and error out at the end
    (relevant_call,) = relevant_calls
    assert relevant_call.result[0] is False
