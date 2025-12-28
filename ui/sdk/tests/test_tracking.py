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

import functools
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List

import pytest
from hamilton_sdk import driver
from hamilton_sdk.api.clients import HamiltonClient
from hamilton_sdk.api.projecttypes import GitInfo
from hamilton_sdk.tracking.runs import TrackingState
from hamilton_sdk.tracking.trackingtypes import Status, TaskRun

from hamilton import base
from hamilton.io.materialization import to

import tests.resources.basic_dag_with_config


# Yeah, I should probably use a mock library but this is simple and does what I want
def track_calls(fn: Callable):
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        setattr(self, f"{fn.__name__}_latest_kwargs", kwargs)
        setattr(self, f"{fn.__name__}_latest_args", args)
        setattr(self, f"{fn.__name__}_call_count", getattr(fn, "call_count", 0) + 1)
        return fn(self, *args, **kwargs)

    return wrapper


class MockHamiltonClient(HamiltonClient):
    """Basic no-op Hamilton client -- mocks out the above Hamilton client for testing"""

    def __init__(self, *args, **kwargs):
        pass

    @track_calls
    def validate_auth(self):
        pass

    @track_calls
    def project_exists(self, project_id: int) -> bool:
        return True

    @track_calls
    def register_dag_template_if_not_exists(
        self,
        project_id: int,
        dag_hash: str,
        code_hash: str,
        nodes: List[dict],
        code_artifacts: List[dict],
        name: str,
        config: dict,
        tags: Dict[str, Any],
        code: List[dict],
        vcs_info: GitInfo,
    ):
        return 1

    @track_calls
    def create_and_start_dag_run(
        self, dag_template_id: int, tags: Dict[str, str], inputs: Dict[str, Any], outputs: List[str]
    ) -> int:
        return 100

    @track_calls
    def update_tasks(
        self,
        dag_run_id: int,
        attributes: List[dict],
        task_updates: List[dict],
        in_samples: List[bool] = None,
    ):
        pass

    @track_calls
    def log_dag_run_end(self, dag_run_id: int, status: str):
        pass


def test_tracking_state():
    state = TrackingState("test")
    state.clock_start()
    state.update_task(
        task_name="foo",
        task_run=TaskRun(
            node_name="node_1",
            status=Status.RUNNING,
            start_time=datetime.now(timezone.utc),
        ),
    )
    task = state.task_map["foo"]
    task.end_time = datetime.now(timezone.utc)
    task.status = Status.SUCCESS
    state.update_task(task_name="foo", task_run=task)
    state.clock_end(Status.SUCCESS)
    run = state.get()
    assert len(run.tasks) == 1
    assert run.status == Status.SUCCESS
    assert run.run_id == "test"
    assert run.tasks[0].status == Status.SUCCESS


def test_tracking_auto_initializes():
    dr = driver.Driver(
        {"foo": "baz"},
        tests.resources.basic_dag_with_config,
        project_id=1,
        api_key="foo",
        username="elijah@dagworks.io",
        client_factory=MockHamiltonClient,
        adapter=base.SimplePythonGraphAdapter(result_builder=base.DictResult()),
        dag_name="test-tracking-auto-initializes",
    )
    dr.execute(final_vars=["c"], inputs={"a": 1})
    assert dr.initialized


def test_tracking_doesnt_break_standard_execution():
    dr = driver.Driver(
        {"foo": "baz"},
        tests.resources.basic_dag_with_config,
        project_id=1,
        api_key="foo",
        username="elijah@dagworks.io",
        client_factory=MockHamiltonClient,
        adapter=base.SimplePythonGraphAdapter(result_builder=base.DictResult()),
        dag_name="test-tracking-doesnt-break-standard-execution",
    )
    result = dr.execute(final_vars=["c"], inputs={"a": 1})
    assert result["c"] == 6  # 2 + 3 + 1


def test_tracking_apis_get_called():
    """Just tests that the API methods get called
    This method of testing is slightly brittle (kwargs versus args) but will do for now.
    """
    dr = driver.Driver(
        {"foo": "baz"},
        tests.resources.basic_dag_with_config,
        project_id=1,
        api_key="foo",
        username="elijah@dagworks.io",
        client_factory=MockHamiltonClient,
        adapter=base.SimplePythonGraphAdapter(result_builder=base.DictResult()),
        dag_name="test-tracking-apis-get-called",
    )
    dr.initialize()
    client = dr.client

    assert client.validate_auth_call_count == 1
    assert client.validate_auth_latest_args == ()
    assert client.validate_auth_latest_kwargs == {}

    assert client.project_exists_call_count == 1
    assert client.project_exists_latest_args == (1,)
    assert client.project_exists_latest_kwargs == {}

    dr.execute(final_vars=["c"], inputs={"a": 1})
    assert client.create_and_start_dag_run_call_count == 1
    assert client.update_tasks_call_count > 0  # We may have multiple in the future
    assert len(client.update_tasks_latest_kwargs["task_updates"]) > 0
    assert client.log_dag_run_end_call_count == 1
    assert client.log_dag_run_end_latest_kwargs["status"] == "SUCCESS"


def test_tracking_apis_no_adapter():
    """Just tests that the API methods get called
    This method of testing is slightly brittle (kwargs versus args) but will do for now.
    """
    dr = driver.Driver(
        {"foo": "baz"},
        tests.resources.basic_dag_with_config,
        project_id=1,
        api_key="foo",
        username="elijah@dagworks.io",
        client_factory=MockHamiltonClient,
        dag_name="test-tracking-apis-get-called",
    )
    dr.initialize()
    client = dr.client

    assert client.validate_auth_call_count == 1
    assert client.validate_auth_latest_args == ()
    assert client.validate_auth_latest_kwargs == {}

    assert client.project_exists_call_count == 1
    assert client.project_exists_latest_args == (1,)
    assert client.project_exists_latest_kwargs == {}

    dr.execute(final_vars=["c"], inputs={"a": 1})
    assert client.create_and_start_dag_run_call_count == 1
    assert client.update_tasks_call_count > 0
    assert len(client.update_tasks_latest_kwargs["task_updates"]) > 0
    assert client.log_dag_run_end_call_count == 1
    assert client.log_dag_run_end_latest_kwargs["status"] == "SUCCESS"


def test_tracking_apis_get_called_failure():
    """Just tests that the API methods get called
    This method of testing is slightly brittle (kwargs versus args) but will do for now.
    """
    dr = driver.Driver(
        {"foo": "baz"},
        tests.resources.basic_dag_with_config,
        project_id=1,
        api_key="foo",
        username="elijah@dagworks.io",
        client_factory=MockHamiltonClient,
        adapter=base.SimplePythonGraphAdapter(result_builder=base.DictResult()),
        dag_name="test-tracking-apis-get-called",
    )
    dr.initialize()
    client = dr.client

    assert client.validate_auth_call_count == 1
    assert client.validate_auth_latest_args == ()
    assert client.validate_auth_latest_kwargs == {}

    assert client.project_exists_call_count == 1
    assert client.project_exists_latest_args == (1,)
    assert client.project_exists_latest_kwargs == {}
    with pytest.raises(ValueError):
        dr.execute(final_vars=["c"], inputs={"a": 1, "should_fail": True})
    assert client.create_and_start_dag_run_call_count == 1
    assert client.update_tasks_call_count > 0  # We may have multiple in the future
    assert len(client.update_tasks_latest_kwargs["task_updates"]) > 0
    assert client.log_dag_run_end_call_count == 1
    assert client.log_dag_run_end_latest_kwargs["status"] == "FAILURE"


def test_tracking_apis_get_called_materialize():
    """Just tests that the API methods get called
    This method of testing is slightly brittle (kwargs versus args) but will do for now.
    """
    dr = driver.Driver(
        {"foo": "baz"},
        tests.resources.basic_dag_with_config,
        project_id=1,
        api_key="foo",
        username="elijah@dagworks.io",
        client_factory=MockHamiltonClient,
        adapter=base.SimplePythonGraphAdapter(result_builder=base.DictResult()),
        dag_name="test-tracking-apis-get-called",
    )
    dr.initialize()
    client = dr.client

    assert client.validate_auth_call_count == 1
    assert client.validate_auth_latest_args == ()
    assert client.validate_auth_latest_kwargs == {}

    assert client.project_exists_call_count == 1
    assert client.project_exists_latest_args == (1,)
    assert client.project_exists_latest_kwargs == {}

    # quick test to ensure that materialize works
    # TODO _- te
    dr.materialize(to.memory(id="test_saver", dependencies=["c"]), inputs={"a": 1})
    assert client.create_and_start_dag_run_call_count == 1
    assert client.update_tasks_call_count > 0  # We may have multiple in the future
    assert len(client.update_tasks_latest_kwargs["task_updates"]) > 0
    assert client.log_dag_run_end_call_count == 1
    assert client.log_dag_run_end_latest_kwargs["status"] == "SUCCESS"


class NonSerializable:
    def __str__(self):
        return "non-serializable-string-rep"

    def __repr__(self):
        return self.__str__()


@pytest.mark.parametrize(
    "config,expected",
    [
        ({"foo": "bar"}, {"foo": "bar"}),
        ({"foo": NonSerializable()}, {"foo": "non-serializable-string-rep"}),
        ({"foo": {"bar": "baz"}}, {"foo": {"bar": "baz"}}),
        ({"foo": {"bar": NonSerializable()}}, {"foo": {"bar": "non-serializable-string-rep"}}),
        (None, {}),
    ],
)
def test_json_filter_config(config, expected):
    assert driver.filter_json_dict_to_serializable(config) == expected
