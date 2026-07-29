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

"""Tests for https://github.com/apache/hamilton/issues/1150.

The result builder is not a graph node -- the sync driver runs it after
``raw_execute`` -- so the UI never showed the combined object ``execute()``
returns. The HamiltonTracker now synthesizes a ``__result_builder`` node
(classified ``result_builder``) and reports the built result as its output.
"""

import asyncio
import functools
from collections.abc import Callable
from typing import Any

import pytest

from hamilton import async_driver, base
from hamilton import driver as h_driver
from hamilton_sdk import adapters
from hamilton_sdk.api import clients
from hamilton_sdk.api.projecttypes import GitInfo
from hamilton_sdk.driver import RESULT_BUILDER_NODE_NAME

import tests.resources.basic_dag_with_config
from tests.test_tracking import MockHamiltonClient


def _make_driver(dag_name: str, with_result_builder: bool = True) -> h_driver.Driver:
    tracker = adapters.HamiltonTracker(
        project_id=1,
        username="repro@example.com",
        dag_name=dag_name,
        client_factory=MockHamiltonClient,
        api_key="foo",
    )
    extra_adapters = [base.DictResult()] if with_result_builder else []
    return (
        h_driver.Builder()
        .with_config({"foo": "baz"})  # selects b__2 (a + 2); with a=1 -> b=3, c=6
        .with_modules(tests.resources.basic_dag_with_config)
        .with_adapters(tracker, *extra_adapters)
        .build()
    )


def _registered_nodes(client: MockHamiltonClient) -> dict[str, list[str]]:
    """name -> classifications for the node list the tracker registered."""
    nodes = client.register_dag_template_if_not_exists_latest_kwargs["nodes"]
    return {n["name"]: n.get("classifications", []) for n in nodes}


def _client(dr: h_driver.Driver) -> MockHamiltonClient:
    (tracker,) = [a for a in dr.adapter.adapters if isinstance(a, adapters.HamiltonTracker)]
    return tracker.client


def test_result_builder_node_is_tracked():
    dr = _make_driver("repro-execute")
    result = dr.execute(final_vars=["b", "c"], inputs={"a": 1})
    assert result == {"b": 3, "c": 6}
    client = _client(dr)

    # the synthetic node is registered in the DAG template, correctly classified
    nodes = _registered_nodes(client)
    assert RESULT_BUILDER_NODE_NAME in nodes
    assert nodes[RESULT_BUILDER_NODE_NAME] == ["result_builder"]

    # the combined result is reported as that node's output: the builder update is
    # the last update_tasks call (it happens right before log_dag_run_end)
    last = client.update_tasks_latest_kwargs
    task_update = last["task_updates"][0]
    assert task_update["node_template_name"] == RESULT_BUILDER_NODE_NAME
    assert task_update["realized_dependencies"] == ["b", "c"]
    assert task_update["status"].value == "SUCCESS"
    assert last["attributes"][0]["name"] == "result_summary"


def test_no_result_builder_no_synthetic_node():
    dr = _make_driver("repro-no-builder", with_result_builder=False)
    dr.execute(final_vars=["b", "c"], inputs={"a": 1})
    client = _client(dr)

    nodes = _registered_nodes(client)
    assert RESULT_BUILDER_NODE_NAME not in nodes
    # the last update_tasks call is a normal node update, not a builder one
    last = client.update_tasks_latest_kwargs
    assert last["task_updates"][0]["node_template_name"] != RESULT_BUILDER_NODE_NAME


def test_failed_run_emits_no_builder_update():
    dr = _make_driver("repro-failure")
    with pytest.raises(ValueError):
        # missing required input "a" -> execution fails
        dr.execute(final_vars=["b", "c"], inputs={})
    client = _client(dr)

    last = getattr(client, "update_tasks_latest_kwargs", None)
    if last is not None:  # nothing may have run at all
        assert last["task_updates"][0]["node_template_name"] != RESULT_BUILDER_NODE_NAME
    assert client.log_dag_run_end_latest_kwargs["status"] == "FAILURE"


class _StrResult(base.DictResult):
    """Builder whose output type (str) differs from the raw node dict."""

    @staticmethod
    def build_result(**outputs):
        return str(outputs)

    def output_type(self):
        return str


def test_raw_execute_emits_no_builder_update():
    """Deprecated raw_execute() never runs the builder -- the tracker must not
    report a builder execution (it only sees the raw node dict)."""
    tracker = adapters.HamiltonTracker(
        project_id=1,
        username="repro@example.com",
        dag_name="repro-raw-execute",
        client_factory=MockHamiltonClient,
        api_key="foo",
    )
    dr = (
        h_driver.Builder()
        .with_config({"foo": "baz"})
        .with_modules(tests.resources.basic_dag_with_config)
        .with_adapters(tracker, _StrResult())
        .build()
    )

    dr.raw_execute(["b", "c"], inputs={"a": 1})  # logs a deprecation warning
    last = tracker.client.update_tasks_latest_kwargs
    assert last["task_updates"][0]["node_template_name"] != RESULT_BUILDER_NODE_NAME

    # sanity check: the same driver's execute() path does report the builder
    result = dr.execute(final_vars=["b", "c"], inputs={"a": 1})
    assert isinstance(result, str)
    last = tracker.client.update_tasks_latest_kwargs
    assert last["task_updates"][0]["node_template_name"] == RESULT_BUILDER_NODE_NAME


# Same trick as tests.test_tracking.track_calls, for async methods.
def track_async_calls(fn: Callable):
    @functools.wraps(fn)
    async def wrapper(self, *args, **kwargs):
        setattr(self, f"{fn.__name__}_latest_kwargs", kwargs)
        setattr(self, f"{fn.__name__}_latest_args", args)
        setattr(self, f"{fn.__name__}_call_count", getattr(fn, "call_count", 0) + 1)
        return await fn(self, *args, **kwargs)

    return wrapper


class MockAsyncHamiltonClient(clients.BasicAsynchronousHamiltonClient):
    """Basic no-op async Hamilton client, mirroring MockHamiltonClient."""

    def __init__(self, *args, **kwargs):
        pass

    @track_async_calls
    async def ainit(self):
        pass

    @track_async_calls
    async def validate_auth(self):
        pass

    @track_async_calls
    async def project_exists(self, project_id: int) -> bool:
        return True

    @track_async_calls
    async def register_dag_template_if_not_exists(
        self,
        project_id: int,
        dag_hash: str,
        code_hash: str,
        nodes: list[dict],
        code_artifacts: list[dict],
        name: str,
        config: dict,
        tags: dict[str, Any],
        code: list[dict],
        vcs_info: GitInfo,
    ):
        return 1

    @track_async_calls
    async def create_and_start_dag_run(
        self, dag_template_id: int, tags: dict[str, str], inputs: dict[str, Any], outputs: list[str]
    ) -> int:
        return 100

    @track_async_calls
    async def update_tasks(
        self,
        dag_run_id: int,
        attributes: list[dict],
        task_updates: list[dict],
        in_samples: list[bool] = None,
    ):
        pass

    @track_async_calls
    async def log_dag_run_end(self, dag_run_id: int, status: str):
        pass


async def _execute_async(dag_name: str) -> tuple[MockAsyncHamiltonClient, dict]:
    tracker = adapters.AsyncHamiltonTracker(
        project_id=1,
        username="repro@example.com",
        dag_name=dag_name,
        client_factory=MockAsyncHamiltonClient,
        api_key="foo",
    )
    await tracker.ainit()
    dr = await (
        async_driver.Builder()
        .with_config({"foo": "baz"})
        .with_modules(tests.resources.basic_dag_with_config)
        .with_adapters(tracker, base.DictResult())
        .build()
    )
    result = await dr.execute(final_vars=["b", "c"], inputs={"a": 1})
    return tracker.client, result


def test_async_result_builder_node_is_tracked():
    client, result = asyncio.run(_execute_async("repro-async-execute"))
    assert result == {"b": 3, "c": 6}

    # the synthetic node is registered in the DAG template, correctly classified
    nodes = _registered_nodes(client)
    assert RESULT_BUILDER_NODE_NAME in nodes
    assert nodes[RESULT_BUILDER_NODE_NAME] == ["result_builder"]

    # the async driver fires post_graph_execute *before* do_build_result, so the
    # tracker can only report a status-only update (no result summary) -- it is
    # still the last update_tasks call, right before log_dag_run_end
    last = client.update_tasks_latest_kwargs
    task_update = last["task_updates"][0]
    assert task_update["node_template_name"] == RESULT_BUILDER_NODE_NAME
    assert task_update["realized_dependencies"] == ["b", "c"]
    assert task_update["status"].value == "SUCCESS"
    assert last["attributes"] == [None]
    assert client.log_dag_run_end_latest_kwargs["status"] == "SUCCESS"
