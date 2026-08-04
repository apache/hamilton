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

import asyncio
import os.path
from types import SimpleNamespace

import pytest
from hamilton_sdk import adapters

from hamilton import driver, lifecycle
from hamilton.io.materialization import to

import tests.resources.basic_dag_with_config
import tests.resources.dag_with_reserved_node_name
import tests.resources.parallel_dag
import tests.resources.parallel_dag_error
from tests import test_tracking

adapter_kwargs = dict(
    project_id=19319,
    api_key="l-PlUq02JLQR6rAvO4x7VTttNTtprj1Tz5zBZ0ARpQ4olb8TK4hlgY2pennFhvsR1DxpYMQ-TLm0JknXVn7y9A",
    username="stefank@cs.stanford.edu",
    tags={"env": "dev", "status": "development"},
    client_factory=test_tracking.MockHamiltonClient,
)


def test_adapters():
    kwargs = adapter_kwargs | dict(
        dag_name="test_dag",
    )
    lifecycle_adapters = [adapters.HamiltonTracker(**kwargs)]
    dr = (
        driver.Builder()
        .with_modules(tests.resources.basic_dag_with_config)
        .with_config({"foo": "baz"})
        .with_adapters(*lifecycle_adapters)
        .build()
    )
    result = dr.execute(final_vars=["a", "b", "c"], inputs={"a": 1})
    assert result == {"a": 1, "b": 3, "c": 6}


class RecordingClient(test_tracking.MockHamiltonClient):
    """Mock client that keeps every task update and attribute, not just the latest."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.all_task_updates = []
        self.all_attributes = []

    def update_tasks(self, dag_run_id, attributes, task_updates, in_samples=None):
        self.all_task_updates.extend(task_updates)
        self.all_attributes.extend(attributes)


def _run_and_record(final_vars, inputs, client, *extra_adapters):
    tracker = adapters.HamiltonTracker(
        **(
            adapter_kwargs
            | dict(dag_name="result_builder_dag", client_factory=lambda *a, **kw: client)
        )
    )
    dr = (
        driver.Builder()
        .with_modules(tests.resources.basic_dag_with_config)
        .with_config({"foo": "baz"})
        .with_adapters(tracker, *extra_adapters)
        .build()
    )
    return dr.execute(final_vars=final_vars, inputs=inputs)


def _emitted_result_builder_tasks(client):
    return [u for u in client.all_task_updates if u["node_name"] == "_result_builder"]


def test_result_builder_task_run_is_emitted():
    """A successful run emits a _result_builder task whose deps are the requested outputs."""
    client = RecordingClient()
    _run_and_record(["a", "b", "c"], {"a": 1}, client)

    emitted = _emitted_result_builder_tasks(client)
    assert len(emitted) == 1
    assert emitted[0]["realized_dependencies"] == ["a", "b", "c"]
    assert emitted[0]["node_template_name"] == "_result_builder"
    assert emitted[0]["status"] == adapters.Status.SUCCESS


def test_no_result_builder_task_run_when_the_name_is_taken():
    """The template is skipped on a collision, so the task run is skipped with it.

    Emitting anyway would post a task update keyed on the user's own node of that name.
    """
    client = RecordingClient()
    tracker = adapters.HamiltonTracker(
        **(
            adapter_kwargs
            | dict(dag_name="reserved_name_dag", client_factory=lambda *a, **kw: client)
        )
    )
    dr = (
        driver.Builder()
        .with_modules(tests.resources.dag_with_reserved_node_name)
        .with_adapters(tracker)
        .build()
    )
    assert dr.execute(final_vars=["uses_the_reserved_name"], inputs={"_result_builder": 1}) == {
        "uses_the_reserved_name": 2
    }

    assert not _emitted_result_builder_tasks(client)


def test_result_builder_task_run_carries_a_result_summary():
    """The combined result is profiled, which is the point of the node.

    The other tests assert on task updates; this one asserts on the attributes, since a
    node that renders with no data observability would satisfy all of them.
    """
    client = RecordingClient()
    _run_and_record(["a", "b", "c"], {"a": 1}, client)

    summaries = [
        a
        # pre_node_execute sends a literal [None] attribute, so entries can be empty
        for a in client.all_attributes
        if a and a["node_name"] == "_result_builder" and a["name"] == "result_summary"
    ]
    assert len(summaries) == 1
    assert summaries[0]["attribute_role"] == "result_summary"
    # process_result profiled the built dict rather than falling back to a failure summary.
    assert summaries[0]["type"] == "dict"
    assert summaries[0]["value"]["value"].keys() == {"a", "b", "c"}


def test_result_builder_task_run_not_emitted_on_failure():
    """A failed run gets no result-builder task, so the UI shows not-executed."""
    client = RecordingClient()
    with pytest.raises(Exception):
        _run_and_record(["c"], {"a": 1, "should_fail": True}, client)

    assert not _emitted_result_builder_tasks(client)


def test_result_builder_failure_does_not_break_the_run(caplog):
    """It runs just before `log_dag_run_end`, so an exception escaping here would leave an
    otherwise-successful run rendering as still-running forever.
    """

    class BrokenClient(RecordingClient):
        def update_tasks(self, dag_run_id, attributes, task_updates, in_samples=None):
            if any(u["node_name"] == "_result_builder" for u in task_updates):
                raise RuntimeError("tracking server is down")
            super().update_tasks(dag_run_id, attributes, task_updates, in_samples)

    client = BrokenClient()
    assert _run_and_record(["a", "b", "c"], {"a": 1}, client) == {"a": 1, "b": 3, "c": 6}
    assert client.log_dag_run_end_latest_kwargs["status"] == adapters.Status.SUCCESS.value
    assert "Failed to emit the _result_builder task run." in caplog.text


class SideEffectResultBuilder(lifecycle.ResultBuilder):
    """A result builder that has a side effect and returns nothing -- e.g. saves to disk."""

    def build_result(self, **outputs):
        return None


def test_result_builder_task_run_is_emitted_when_the_builder_returns_none():
    """Emitted on every successful run, even when the built result is None."""
    client = RecordingClient()
    assert _run_and_record(["a", "b", "c"], {"a": 1}, client, SideEffectResultBuilder()) is None

    emitted = _emitted_result_builder_tasks(client)
    assert len(emitted) == 1
    assert emitted[0]["status"] == adapters.Status.SUCCESS
    assert emitted[0]["realized_dependencies"] == ["a", "b", "c"]


def test_result_builder_dependencies_under_materialize(tmp_path):
    """materialize() asks pre_graph_execute for final_vars + materializer_vars, but hands
    post_graph_execute only the final_vars slice -- so the recorded deps must not name the
    materializer.
    """
    client = RecordingClient()
    tracker = adapters.HamiltonTracker(
        **(
            adapter_kwargs
            | dict(dag_name="materialize_dag", client_factory=lambda *a, **kw: client)
        )
    )
    dr = (
        driver.Builder()
        .with_modules(tests.resources.basic_dag_with_config)
        .with_config({"foo": "baz"})
        .with_adapters(tracker)
        .build()
    )
    dr.materialize(
        to.pickle(id="save_c", dependencies=["c"], path=str(tmp_path / "c.pkl")),
        additional_vars=["a", "b"],
        inputs={"a": 1},
    )

    emitted = _emitted_result_builder_tasks(client)
    assert len(emitted) == 1
    assert emitted[0]["realized_dependencies"] == ["a", "b"]


def test_result_builder_dependencies_keeps_the_requested_list_for_a_builder_of_its_own_keys():
    """A custom builder's keys are its own, so there is nothing safe to narrow away."""
    assert adapters._result_builder_dependencies({"renamed": 3}, ["a", "b"]) == ["a", "b"]
    assert adapters._result_builder_dependencies({"a": 1, "b": 2}, ["a", "b"]) == ["a", "b"]
    assert adapters._result_builder_dependencies({"a": 1}, ["a", "b"]) == ["a"]


class RecordingAsyncClient(RecordingClient):
    """Async twin of RecordingClient -- the async tracker awaits every client call."""

    async def create_and_start_dag_run(self, **kwargs):
        return 1

    async def update_tasks(self, dag_run_id, attributes, task_updates, in_samples=None):
        self.all_task_updates.extend(task_updates)
        self.all_attributes.extend(attributes)

    async def log_dag_run_end(self, dag_run_id, status):
        pass


def _run_async_graph_hooks(final_vars, results, success):
    """Drives the async tracker's graph hooks directly.

    There is no async DAG fixture here and standing one up would need pytest-asyncio; the
    graph hooks are what carry the result-builder behaviour, so they are what gets exercised.
    The stand-in graph needs an identity and an empty `nodes`; the seeded template cache stands
    in for the `post_graph_construct` this skips.
    """
    client = RecordingAsyncClient()
    tracker = adapters.AsyncHamiltonTracker(
        **(
            adapter_kwargs
            | dict(dag_name="async_result_builder_dag", client_factory=lambda *a, **kw: client)
        )
    )
    graph = SimpleNamespace(nodes={})
    tracker.dag_template_id_cache[id(graph)] = 1

    async def run():
        await tracker.pre_graph_execute("run-1", graph, final_vars, {}, {})
        await tracker.post_graph_execute("run-1", graph, success, None, results)

    asyncio.run(run())
    return client


def test_async_result_builder_task_run_is_emitted():
    """The async tracker emits the same task run as the sync one."""
    client = _run_async_graph_hooks(["a", "b", "c"], {"a": 1, "b": 3, "c": 6}, success=True)

    emitted = _emitted_result_builder_tasks(client)
    assert len(emitted) == 1
    assert emitted[0]["realized_dependencies"] == ["a", "b", "c"]
    assert emitted[0]["node_template_name"] == "_result_builder"
    assert emitted[0]["status"] == adapters.Status.SUCCESS


def test_async_result_builder_task_run_not_emitted_on_failure():
    """A failed run gets no result-builder task -- async side."""
    client = _run_async_graph_hooks(["c"], None, success=False)

    assert not _emitted_result_builder_tasks(client)


def test_parallel_ray():
    """Tests ray works without sampling.
    Doesn't actually check the client - go do that in the UI."""
    ray = pytest.importorskip("ray")

    from hamilton.plugins import h_ray

    kwargs = adapter_kwargs | dict(dag_name="parallel_test_dag", tags={"sampling_rate": "None"})
    lifecycle_adapters = [adapters.HamiltonTracker(**kwargs)]
    remote_executor = h_ray.RayTaskExecutor(None)
    # remote_executor = executors.SynchronousLocalTaskExecutor()
    shutdown = ray.shutdown
    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(remote_executor)  # We only need to specify remote executor
        # The local executor just runs it synchronously
        .with_modules(tests.resources.parallel_dag)
        .with_adapters(*lifecycle_adapters)
        .build()
    )
    data_dir = os.path.join(os.path.dirname(__file__), "resources", "data")
    result = dr.execute(final_vars=["statistics_by_city"], inputs={"data_dir": data_dir})[
        "statistics_by_city"
    ]
    print(result)
    if shutdown:
        shutdown()
    expected_cities = {"barcelona", "berlin", "budapest"}
    for val in result.index.values:
        assert val in expected_cities


def test_parallel_ray_sample():
    """Tests ray works with sampling.
    Doesn't actually check the client - go do that in the UI."""
    ray = pytest.importorskip("ray")

    from hamilton.plugins import h_ray

    special_parallel_sample_strategy = 0.33
    kwargs = adapter_kwargs | dict(
        dag_name="parallel_test_dag", tags={"sampling_rate": str(special_parallel_sample_strategy)}
    )
    lifecycle_adapters = [adapters.HamiltonTracker(**kwargs)]
    lifecycle_adapters[0].special_parallel_sample_strategy = special_parallel_sample_strategy
    remote_executor = h_ray.RayTaskExecutor(None)
    # remote_executor = executors.SynchronousLocalTaskExecutor()
    shutdown = ray.shutdown
    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(remote_executor)  # We only need to specify remote executor
        # The local executor just runs it synchronously
        .with_modules(tests.resources.parallel_dag)
        .with_adapters(*lifecycle_adapters)
        .build()
    )
    data_dir = os.path.join(os.path.dirname(__file__), "resources", "data")
    result = dr.execute(final_vars=["statistics_by_city"], inputs={"data_dir": data_dir})[
        "statistics_by_city"
    ]
    print(result)
    if shutdown:
        shutdown()
    expected_cities = {"barcelona", "berlin", "budapest"}
    for val in result.index.values:
        assert val in expected_cities


def test_parallel_ray_sample_error():
    """Tests error returning a sample.
    Doesn't actually check the client - go do that in the UI."""
    ray = pytest.importorskip("ray")

    from hamilton.plugins import h_ray

    special_parallel_sample_strategy = 0.0
    kwargs = adapter_kwargs | dict(
        dag_name="parallel_test_dag", tags={"sampling_rate": str(special_parallel_sample_strategy)}
    )
    lifecycle_adapters = [adapters.HamiltonTracker(**kwargs)]
    lifecycle_adapters[0].special_parallel_sample_strategy = special_parallel_sample_strategy
    remote_executor = h_ray.RayTaskExecutor(None)
    # remote_executor = executors.SynchronousLocalTaskExecutor()
    shutdown = ray.shutdown
    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(remote_executor)  # We only need to specify remote executor
        # The local executor just runs it synchronously
        .with_modules(tests.resources.parallel_dag_error)
        .with_adapters(*lifecycle_adapters)
        .build()
    )
    data_dir = os.path.join(os.path.dirname(__file__), "resources", "data")
    with pytest.raises(ValueError):
        dr.execute(final_vars=["statistics_by_city"], inputs={"data_dir": data_dir})
    if shutdown:
        shutdown()


if __name__ == "__main__":
    # test_adapters()

    # logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    # test_async()
    # test_parallel_ray_sample()
    # test_parallel_ray()
    test_parallel_ray_sample_error()
