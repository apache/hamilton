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

import dataclasses
import functools
import inspect
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Tuple

from hamilton import node
from hamilton.execution.grouping import NodeGroupPurpose
from hamilton.graph import FunctionGraph
from hamilton.lifecycle.base import (
    BaseDoBuildResult,
    BaseDoNodeExecute,
    BaseDoRemoteExecute,
    BaseDoValidateInput,
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
    BaseValidateGraph,
    BaseValidateNode,
    LifecycleAdapterSet,
)
from hamilton.node import Node


@dataclasses.dataclass
class HookCall:
    sequence_number: int
    name: str
    fn: Callable
    bound_kwargs: Dict[str, Any]
    result: Any


class SentinelException(Exception):
    pass


# Allows us to track the order in which multiple lifecycle hooks are called
# This ensures that we can get order of call across operations
# We'll want to test for order, not absolute position, as it is global
sequence_number = 0


# This is slightly hacky, but its a quick way to decorate the lifecycle hooks
class ExtendToTrackCalls:
    def __init__(self, name: str):
        # We just pass in self, cause why not?
        adapter_set = LifecycleAdapterSet(self)
        for lifecycle_step, _ in {
            **adapter_set.sync_methods,
            **adapter_set.async_methods,
            **adapter_set.sync_hooks,
            **adapter_set.async_hooks,
            **adapter_set.sync_validators,
        }.items():
            # We know there's just one in this case
            setattr(self, lifecycle_step, self._wrap_fn(getattr(self, lifecycle_step)))
        self._calls = []
        self._name = name

    def _wrap_fn(self, fn: Callable):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            global sequence_number
            sequence_number += 1
            sig = inspect.signature(fn)
            bound = sig.bind(*args, **kwargs)
            out = fn(*args, **kwargs)
            self._calls.append(HookCall(sequence_number, self._name, fn, bound.arguments, out))
            return out

        return wrapped

    @property
    def calls(self) -> List[HookCall]:
        return self._calls

    @property
    def name(self):
        return self._name


class TrackingPreDoAnythingHook(BasePreDoAnythingHook, ExtendToTrackCalls):
    def pre_do_anything(self):
        pass


class TrackingPostGraphConstructHook(ExtendToTrackCalls, BasePostGraphConstruct):
    def post_graph_construct(
        self, graph: FunctionGraph, modules: List[ModuleType], config: Dict[str, Any]
    ):
        pass


class TrackingPreGraphExecuteHook(ExtendToTrackCalls, BasePreGraphExecute):
    def pre_graph_execute(
        self,
        run_id: str,
        graph: FunctionGraph,
        final_vars: List[str],
        inputs: Dict[str, Any],
        overrides: Dict[str, Any],
    ):
        pass


class TrackingPostTaskGroupHook(ExtendToTrackCalls, BasePostTaskGroup):
    def post_task_group(self, run_id: str, task_ids: List[str]):
        pass


class TrackingPreTaskExecuteHook(ExtendToTrackCalls, BasePreTaskExecute):
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


class TrackingPreNodeExecuteHook(ExtendToTrackCalls, BasePreNodeExecute):
    def pre_node_execute(
        self, run_id: str, node_: Node, kwargs: Dict[str, Any], task_id: Optional[str] = None
    ):
        pass


class TrackingPostNodeExecuteHook(ExtendToTrackCalls, BasePostNodeExecute):
    def post_node_execute(
        self,
        run_id: str,
        node_: Node,
        kwargs: Dict[str, Any],
        success: bool,
        error: Optional[Exception],
        result: Any,
        task_id: Optional[str] = None,
    ):
        pass


class TrackingPreTaskSubmissionHook(ExtendToTrackCalls, BasePreTaskSubmission):
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


class TrackingPostTaskReturnHook(ExtendToTrackCalls, BasePostTaskReturn):
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


class TrackingPostTaskExecuteHook(ExtendToTrackCalls, BasePostTaskExecute):
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


class TrackingPostTaskExpandHook(ExtendToTrackCalls, BasePostTaskExpand):
    def post_task_expand(self, run_id: str, task_id: str, parameters: Dict[str, Any]):
        pass


class TrackingPostGraphExecuteHook(ExtendToTrackCalls, BasePostGraphExecute):
    def post_graph_execute(
        self,
        run_id: str,
        graph: FunctionGraph,
        success: bool,
        error: Optional[Exception],
        results: Optional[Dict[str, Any]],
    ):
        pass


class TrackingDoValidateInputMethod(ExtendToTrackCalls, BaseDoValidateInput):
    def __init__(self, name: str, valid: bool = True):
        super().__init__(name)
        self._valid = valid

    def do_validate_input(self, node_type: type, input_value: Any) -> bool:
        return self._valid


class TrackingDoNodeExecuteHook(ExtendToTrackCalls, BaseDoNodeExecute):
    def __init__(self, name: str, additional_value: int):
        super().__init__(name)
        self._additional_value = additional_value

    def do_node_execute(
        self, run_id: str, node_: node.Node, kwargs: Dict[str, Any], task_id: Optional[str] = None
    ) -> Any:
        if node_.type == int and node_.name != "n_iters":
            return node_(**kwargs) + self._additional_value
        return node_(**kwargs)


class TrackingDoRemoteExecuteHook(ExtendToTrackCalls, BaseDoRemoteExecute):
    def __init__(self, name: str, additional_value: int):
        super().__init__(name)
        self._additional_value = additional_value

    def do_remote_execute(
        self,
        node: "node.Node",
        execute_lifecycle_for_node: Callable,
        **kwargs: Dict[str, Any],
    ) -> Any:
        node_ = node
        if node_.type == int and node_.name != "n_iters":
            return execute_lifecycle_for_node(**kwargs) + self._additional_value
        return execute_lifecycle_for_node(**kwargs)


class TrackingDoBuildResultMethod(ExtendToTrackCalls, BaseDoBuildResult):
    def __init__(self, name: str, result: Any):
        super().__init__(name)
        self._result = result

    def do_build_result(self, outputs: Dict[str, Any]) -> Any:
        return self._result


class TrackingValidateNodeValidator(ExtendToTrackCalls, BaseValidateNode):
    def __init__(self, name: str, valid: bool, message: Optional[str]):
        super().__init__(name)
        self._valid = valid
        self._message = message

    def validate_node(self, *, created_node: node.Node) -> Tuple[bool, Optional[str]]:
        return self._valid, self._message


class TrackingValidateGraphValidator(ExtendToTrackCalls, BaseValidateGraph):
    def __init__(self, name: str, valid: bool, message: Optional[str]):
        super().__init__(name)
        self._valid = valid
        self._message = message

    def validate_graph(
        self, *, graph: "FunctionGraph", modules: List[ModuleType], config: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        return self._valid, self._message
