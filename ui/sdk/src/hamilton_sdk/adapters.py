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

import datetime
import hashlib
import logging
import os
import random
import traceback
from datetime import timezone

# Compatibility for Python < 3.11
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from types import ModuleType
from typing import Any, Optional
from collections.abc import Callable, Mapping

from hamilton import graph as h_graph
from hamilton import node
from hamilton.data_quality import base as dq_base
from hamilton.lifecycle import base

from hamilton_sdk import driver
from hamilton_sdk.api import clients, constants
from hamilton_sdk.tracking import runs
from hamilton_sdk.tracking.runs import Status, TrackingState
from hamilton_sdk.tracking.trackingtypes import TaskRun

logger = logging.getLogger(__name__)


def get_node_name(node_: node.Node, task_id: Optional[str]) -> str:
    if task_id is not None:
        return f"{task_id}-{node_.name}"
    return node_.name


LONG_SCALE = float(0xFFFFFFFFFFFFFFF)


def _result_attribute(node_name: str, name: str, observation: dict) -> dict:
    """Shapes one observation into the attribute dict the tracking API expects."""
    return dict(
        node_name=node_name,
        name=name,
        type=observation["observability_type"],
        # 0.0.3 -> 3
        schema_version=int(observation["observability_schema_version"].split(".")[-1]),
        value=observation["observability_value"],
        attribute_role="result_summary",
    )


def _result_attributes(
    node_name: str, result_summary: dict, schema: Optional[dict], additional: list[dict]
) -> list[dict]:
    """Builds the attribute list for a successful task run.

    `result_summary` is first because the order influences UI display order.
    """
    others = ([schema] if schema is not None else []) + additional
    return [_result_attribute(node_name, "result_summary", result_summary)] + [
        # retrieve name if specified
        _result_attribute(node_name, other.get("name", f"Attribute {i + 1}"), other)
        for i, other in enumerate(others)
    ]


def _observability_failure_summary() -> dict:
    """The result summary used when profiling the result did not produce one."""
    return {
        "observability_type": "observability_failure",
        "observability_schema_version": "0.0.3",
        "observability_value": {
            "type": str(str),
            "value": "Failed to process result.",
        },
    }


def _result_builder_dependencies(results: Any, final_vars: list[str]) -> list[str]:
    """The requested outputs that actually reached the result being reported.

    Narrowing is only sound when the result is keyed by node name, as ``DictResult`` and the raw
    dict ``materialize`` hands over both are. A result that cannot say what went into it -- a
    dataframe, a custom builder's own dict -- keeps the full list rather than be credited with
    nothing.

    :param results: What the driver passed to ``post_graph_execute``.
    :param final_vars: The outputs requested at ``pre_graph_execute``.
    :return: The node names to record as this run's dependencies, always a subset of
        ``final_vars``.
    """
    if isinstance(results, Mapping) and set(results).issubset(final_vars):
        return [var for var in final_vars if var in results]
    return final_vars


def _result_builder_payload(
    results: Any, timestamp: datetime.datetime, final_vars: list[str]
) -> tuple[TaskRun, list[dict], dict]:
    """Builds everything the synthetic ``_result_builder`` task run needs to be sent.

    Free of I/O, so the sync and async trackers can share it and each send it their own way.

    Not guarded on ``results`` being non-None: a result builder with a side effect and no return
    value still ran. See "The result builder node" in docs/hamilton-ui/ui.rst for which execution
    paths hand this a built result and which hand it the raw output dict.

    :param results: The combined result the driver produced.
    :param timestamp: Time to stamp the task run with -- the builder runs between the last
        node and ``post_graph_execute``, and its duration is not observable.
    :param final_vars: The outputs this run asked for, used where the result cannot say.
    :return: The task run, its attributes, and the task update to send.
    """
    node_name = driver.RESULT_BUILDER_NODE_NAME
    # process_result only reads `.name` and `.tags`; there is no real node to pass.
    stand_in = node.Node(node_name, Any, callabl=lambda: None)
    task_run = TaskRun(node_name=node_name, is_in_sample=True)
    task_run.status = Status.SUCCESS
    task_run.start_time = timestamp
    task_run.end_time = timestamp
    task_run.result_type = type(results)
    result_summary, schema, additional_attributes = runs.process_result(results, stand_in)
    if result_summary is None:
        result_summary = _observability_failure_summary()
    task_run.result_summary = result_summary
    attributes = _result_attributes(node_name, result_summary, schema, additional_attributes)
    task_update = dict(
        node_template_name=node_name,
        node_name=node_name,
        realized_dependencies=_result_builder_dependencies(results, final_vars),
        status=task_run.status,
        start_time=task_run.start_time,
        end_time=task_run.end_time,
    )
    return task_run, attributes, task_update


class HamiltonTracker(
    base.BasePostGraphConstruct,
    base.BasePreGraphExecute,
    base.BasePreNodeExecute,
    base.BasePostNodeExecute,
    base.BasePostGraphExecute,
):
    def __init__(
        self,
        project_id: int,
        username: str,
        dag_name: str,
        tags: dict[str, str] = None,
        client_factory: Callable[
            [str, str, str, str | bool], clients.HamiltonClient
        ] = clients.BasicSynchronousHamiltonClient,
        api_key: str = None,
        hamilton_api_url=os.environ.get("HAMILTON_API_URL", constants.HAMILTON_API_URL),
        hamilton_ui_url=os.environ.get("HAMILTON_UI_URL", constants.HAMILTON_UI_URL),
        verify: str | bool = True,
    ):
        """This hooks into Hamilton execution to track DAG runs in Hamilton UI.

        :param project_id: the ID of the project
        :param username: the username for the API key.
        :param dag_name: the name of the DAG.
        :param tags: any tags to help curate and organize the DAG
        :param client_factory: a factory to create the client to phone Hamilton with.
        :param api_key: the API key to use. See us if you want to use this.
        :param hamilton_api_url: API endpoint.
        :param hamilton_ui_url: UI Endpoint.
        :param verify: SSL verification to pass-through to requests
        """
        self.project_id = project_id
        self.api_key = api_key
        self.username = username
        self.client = client_factory(api_key, username, hamilton_api_url, verify=verify)
        self.initialized = False
        self.project_version = None
        self.base_tags = tags if tags is not None else {}
        driver.validate_tags(self.base_tags)
        self.dag_name = dag_name
        self.hamilton_ui_url = hamilton_ui_url
        logger.debug("Validating authentication against Hamilton BE API...")
        self.client.validate_auth()
        logger.debug(f"Ensuring project {self.project_id} exists...")
        try:
            self.client.project_exists(self.project_id)
        except clients.UnauthorizedException:
            logger.exception(
                f"Authentication failed. Please check your username and try again. "
                f"Username: {self.username}..."
            )
            raise
        except clients.ResourceDoesNotExistException:
            logger.error(
                f"Project {self.project_id} does not exist/is accessible. Please create it first in the UI! "
                f"You can do so at {self.hamilton_ui_url}/dashboard/projects"
            )
            raise
        self.dag_template_id_cache = {}
        self.tracking_states = {}
        self.dw_run_ids = {}
        self.task_runs = {}
        # requested outputs per run -- the result-builder node's per-run dependencies
        self.final_vars = {}
        super().__init__()
        # set this to a float to sample blocks. 0.1 means 10% of blocks will be sampled.
        # set this to an int to sample blocks by modulo.
        self.special_parallel_sample_strategy = None
        # set this to some constant value if you want to generate the same sample each time.
        # if you're using a float value.
        self.seed = None

    def stop(self):
        """Initiates stop if run in remote environment"""
        self.client.stop()

    def post_graph_construct(
        self, graph: h_graph.FunctionGraph, modules: list[ModuleType], config: dict[str, Any]
    ):
        """Registers the DAG to get an ID."""
        if self.seed is None:
            self.seed = random.random()
        logger.debug("post_graph_construct")
        fg_id = id(graph)
        if fg_id in self.dag_template_id_cache:
            logger.warning("Skipping creation of DAG template as it already exists.")
            return
        module_hash = driver._get_modules_hash(modules)
        vcs_info = driver._derive_version_control_info(module_hash)
        dag_hash = driver.hash_dag(graph, include_result_builder=True)
        code_hash = driver.hash_dag_modules(graph, modules)
        dag_template_id = self.client.register_dag_template_if_not_exists(
            project_id=self.project_id,
            dag_hash=dag_hash,
            code_hash=code_hash,
            name=self.dag_name,
            nodes=driver._extract_node_templates_from_function_graph(
                graph, include_result_builder=True
            ),
            code_artifacts=driver.extract_code_artifacts_from_function_graph(
                graph, vcs_info, vcs_info.local_repo_base_path
            ),
            config=graph.config,
            tags=self.base_tags,
            code=driver._slurp_code(graph, vcs_info.local_repo_base_path),
            vcs_info=vcs_info,
        )
        self.dag_template_id_cache[fg_id] = dag_template_id

    def pre_graph_execute(
        self,
        run_id: str,
        graph: h_graph.FunctionGraph,
        final_vars: list[str],
        inputs: dict[str, Any],
        overrides: dict[str, Any],
    ):
        """Creates a DAG run."""
        logger.debug("pre_graph_execute %s", run_id)
        fg_id = id(graph)
        if fg_id in self.dag_template_id_cache:
            dag_template_id = self.dag_template_id_cache[fg_id]
        else:
            raise ValueError("DAG template ID not found in cache. This should never happen.")
        tracking_state = TrackingState(run_id)
        self.tracking_states[run_id] = tracking_state  # cache
        tracking_state.clock_start()
        dw_run_id = self.client.create_and_start_dag_run(
            dag_template_id=dag_template_id,
            tags=self.base_tags,
            inputs=inputs if inputs is not None else {},
            outputs=final_vars,
        )
        self.dw_run_ids[run_id] = dw_run_id
        self.task_runs[run_id] = {}
        self.final_vars[run_id] = final_vars
        logger.warning(
            f"\nCapturing execution run. Results can be found at "
            f"{self.hamilton_ui_url}/dashboard/project/{self.project_id}/runs/{dw_run_id}\n"
        )
        return dw_run_id

    def pre_node_execute(
        self, run_id: str, node_: node.Node, kwargs: dict[str, Any], task_id: Optional[str] = None
    ):
        """Captures start of node execution."""
        logger.debug("pre_node_execute %s %s", run_id, task_id)
        tracking_state = self.tracking_states[run_id]
        if tracking_state.status == Status.UNINITIALIZED:  # not thread safe?
            tracking_state.update_status(Status.RUNNING)

        in_sample = self.is_in_sample(task_id)
        task_run = TaskRun(node_name=node_.name, is_in_sample=in_sample)
        task_run.status = Status.RUNNING
        task_run.start_time = datetime.datetime.now(UTC)
        tracking_state.update_task(node_.name, task_run)
        self.task_runs[run_id][node_.name] = task_run

        task_update = dict(
            node_template_name=node_.name,
            node_name=get_node_name(node_, task_id),
            realized_dependencies=[dep.name for dep in node_.dependencies],
            status=task_run.status,
            start_time=task_run.start_time,
            end_time=None,
        )
        # we need a 1-1 mapping of updates for the sample stuff to work.
        self.client.update_tasks(
            self.dw_run_ids[run_id],
            attributes=[None],
            task_updates=[task_update],
            in_samples=[task_run.is_in_sample],
        )

    def get_hash(self, block_value: int):
        """Creates a deterministic hash."""
        full_salt = "%s.%s%s" % (self.seed, "DAGWORKS", ".")
        hash_str = "%s%s" % (full_salt, str(block_value))
        hash_str = hash_str.encode("ascii")
        return int(hashlib.sha1(hash_str).hexdigest()[:15], 16)

    def get_deterministic_random(self, block_value: int):
        """Gets a random number between 0 & 1 given the block value."""
        zero_to_one = self.get_hash(block_value) / LONG_SCALE
        return zero_to_one  # should be between 0 and 1

    def is_in_sample(self, task_id: str) -> bool:
        """Determines if what we're tracking is considered in sample.

        This should only be used at the node level right now and is intended
        for parallel blocks that could be quick large.
        """
        if (
            self.special_parallel_sample_strategy is not None
            and task_id is not None
            and task_id.startswith("expand-")
            and "block" in task_id
        ):
            in_sample = False
            block_id = int(task_id.split(".")[1])
            if isinstance(self.special_parallel_sample_strategy, float):
                # if it's a float we want to sample blocks
                if self.get_deterministic_random(block_id) < self.special_parallel_sample_strategy:
                    in_sample = True
            elif isinstance(self.special_parallel_sample_strategy, int):
                # if it's an int we want to take the modulo of the block id so all the
                # nodes for a block will be captured or not.
                if block_id % self.special_parallel_sample_strategy == 0:
                    in_sample = True
            else:
                raise ValueError(
                    f"Unknown special_parallel_sample_strategy: "
                    f"{self.special_parallel_sample_strategy}"
                )
        else:
            in_sample = True
        return in_sample

    def post_node_execute(
        self,
        run_id: str,
        node_: node.Node,
        kwargs: dict[str, Any],
        success: bool,
        error: Optional[Exception],
        result: Optional[Any],
        task_id: Optional[str] = None,
    ):
        """Captures end of node execution."""
        logger.debug("post_node_execute %s %s", run_id, task_id)
        task_run: TaskRun = self.task_runs[run_id][node_.name]
        tracking_state = self.tracking_states[run_id]
        task_run.end_time = datetime.datetime.now(UTC)

        other_results = []
        if success:
            task_run.status = Status.SUCCESS
            task_run.result_type = type(result)
            result_summary, schema, additional_attributes = runs.process_result(result, node_)
            if result_summary is None:
                result_summary = {
                    "observability_type": "observability_failure",
                    "observability_schema_version": "0.0.3",
                    "observability_value": {
                        "type": str(str),
                        "value": "Failed to process result.",
                    },
                }
            other_results = ([schema] if schema is not None else []) + additional_attributes

            task_run.result_summary = result_summary
            task_attr = dict(
                node_name=get_node_name(node_, task_id),
                name="result_summary",
                type=task_run.result_summary["observability_type"],
                # 0.0.3 -> 3
                schema_version=int(
                    task_run.result_summary["observability_schema_version"].split(".")[-1]
                ),
                value=task_run.result_summary["observability_value"],
                attribute_role="result_summary",
            )

        else:
            task_run.status = Status.FAILURE
            task_run.is_in_sample = True  # override any sampling
            if isinstance(error, dq_base.DataValidationError):
                task_run.error = runs.serialize_data_quality_error(error)
            else:
                task_run.error = traceback.format_exception(type(error), error, error.__traceback__)
            task_attr = dict(
                node_name=get_node_name(node_, task_id),
                name="stack_trace",
                type="error",
                schema_version=1,
                value={
                    "stack_trace": task_run.error,
                },
                attribute_role="error",
            )

        # `result_summary` or "error" is first because the order influences UI display order
        attributes = [task_attr]
        for i, other_result in enumerate(other_results):
            other_attr = dict(
                node_name=get_node_name(node_, task_id),
                name=other_result.get("name", f"Attribute {i + 1}"),  # retrieve name if specified
                type=other_result["observability_type"],
                # 0.0.3 -> 3
                schema_version=int(other_result["observability_schema_version"].split(".")[-1]),
                value=other_result["observability_value"],
                attribute_role="result_summary",
            )
            attributes.append(other_attr)
        tracking_state.update_task(node_.name, task_run)
        task_update = dict(
            node_template_name=node_.name,
            node_name=get_node_name(node_, task_id),
            realized_dependencies=[dep.name for dep in node_.dependencies],
            status=task_run.status,
            start_time=task_run.start_time,
            end_time=task_run.end_time,
        )
        self.client.update_tasks(
            self.dw_run_ids[run_id],
            attributes=attributes,
            task_updates=[task_update for _ in attributes],
            in_samples=[task_run.is_in_sample for _ in attributes],
        )

    def _emit_result_builder_task_run(
        self, run_id: str, results: Any, timestamp: datetime.datetime
    ):
        """Emits the task run for the synthetic ``_result_builder`` node.

        Failures are logged and swallowed: this runs before ``log_dag_run_end``, and an
        otherwise-successful run should not be left rendering as still-running because
        profiling or sending the combined result went wrong.
        """
        try:
            task_run, attributes, task_update = _result_builder_payload(
                results, timestamp, self.final_vars.get(run_id, [])
            )
            self.tracking_states[run_id].update_task(task_run.node_name, task_run)
            self.client.update_tasks(
                self.dw_run_ids[run_id],
                attributes=attributes,
                task_updates=[task_update for _ in attributes],
                in_samples=[True for _ in attributes],
            )
        except Exception:
            logger.exception("Failed to emit the %s task run.", driver.RESULT_BUILDER_NODE_NAME)

    def post_graph_execute(
        self,
        run_id: str,
        graph: h_graph.FunctionGraph,
        success: bool,
        error: Optional[Exception],
        results: Optional[dict[str, Any]],
    ):
        """Captures end of DAG execution."""
        logger.debug("post_graph_execute %s", run_id)
        dw_run_id = self.dw_run_ids[run_id]
        tracking_state = self.tracking_states[run_id]
        tracking_state.clock_end(status=Status.SUCCESS if success else Status.FAILURE)
        finally_block_time = datetime.datetime.now(UTC)
        if tracking_state.status != Status.SUCCESS:
            # TODO: figure out how to handle crtl+c stuff
            # -- we are at the mercy of Hamilton here.
            tracking_state.status = Status.FAILURE
            # this assumes the task map only has things that have been processed, not
            # nodes that have yet to be computed.
            for task_name, task_run in tracking_state.task_map.items():
                if task_run.status != Status.SUCCESS:
                    task_run.status = Status.FAILURE
                    task_run.end_time = finally_block_time
                    if task_run.error is None:  # we likely aborted it.
                        # Note if we start to do concurrent execution we'll likely
                        # need to adjust this.
                        task_run.error = ["Run was likely aborted."]
                if task_run.end_time is None and task_run.status == Status.SUCCESS:
                    task_run.end_time = finally_block_time
        elif driver._should_register_result_builder(graph):
            self._emit_result_builder_task_run(run_id, results, finally_block_time)

        self.client.log_dag_run_end(
            dag_run_id=dw_run_id,
            status=tracking_state.status.value,
        )
        logger.warning(
            f"\nCaptured execution run. Results can be found at "
            f"{self.hamilton_ui_url}/dashboard/project/{self.project_id}/runs/{dw_run_id}\n"
        )


class AsyncHamiltonTracker(
    base.BasePostGraphConstructAsync,
    base.BasePreGraphExecuteAsync,
    base.BasePreNodeExecuteAsync,
    base.BasePostNodeExecuteAsync,
    base.BasePostGraphExecuteAsync,
):
    def __init__(
        self,
        project_id: int,
        username: str,
        dag_name: str,
        tags: dict[str, str] = None,
        client_factory: Callable[
            [str, str, str, str | bool], clients.BasicAsynchronousHamiltonClient
        ] = clients.BasicAsynchronousHamiltonClient,
        api_key: str = os.environ.get("HAMILTON_API_KEY", ""),
        hamilton_api_url=os.environ.get("HAMILTON_API_URL", constants.HAMILTON_API_URL),
        hamilton_ui_url=os.environ.get("HAMILTON_UI_URL", constants.HAMILTON_UI_URL),
        verify: str | bool = True,
    ):
        self.project_id = project_id
        self.api_key = api_key
        self.username = username
        self.client = client_factory(api_key, username, hamilton_api_url, verify=verify)
        self.initialized = False
        self.project_version = None
        self.base_tags = tags if tags is not None else {}
        driver.validate_tags(self.base_tags)
        self.dag_name = dag_name
        self.hamilton_ui_url = hamilton_ui_url
        self.dag_template_id_cache = {}
        self.tracking_states = {}
        self.dw_run_ids = {}
        self.task_runs = {}
        # requested outputs per run -- the result-builder node's per-run dependencies
        self.final_vars = {}
        self.initialized = False
        super().__init__()

    async def ainit(self):
        if self.initialized:
            return self
        """You must call this to initialize the tracker."""
        logger.info("Validating authentication against Hamilton BE API...")
        await self.client.validate_auth()
        logger.info(f"Ensuring project {self.project_id} exists...")
        try:
            await self.client.project_exists(self.project_id)
        except clients.UnauthorizedException:
            logger.exception(
                f"Authentication failed. Please check your username and try again. "
                f"Username: {self.username}"
            )
            raise
        except clients.ResourceDoesNotExistException:
            logger.error(
                f"Project {self.project_id} does not exist/is accessible. Please create it first in the UI! "
                f"You can do so at {self.hamilton_ui_url}/dashboard/projects"
            )
            raise
        logger.info("Initializing Hamilton tracker.")
        await self.client.ainit()
        logger.info("Initialized Hamilton tracker.")
        self.initialized = True
        return self

    async def post_graph_construct(
        self, graph: h_graph.FunctionGraph, modules: list[ModuleType], config: dict[str, Any]
    ):
        logger.debug("post_graph_construct")
        fg_id = id(graph)
        if fg_id in self.dag_template_id_cache:
            logger.warning("Skipping creation of DAG template as it already exists.")
            return
        module_hash = driver._get_modules_hash(modules)
        vcs_info = driver._derive_version_control_info(module_hash)
        dag_hash = driver.hash_dag(graph, include_result_builder=True)
        code_hash = driver.hash_dag_modules(graph, modules)
        dag_template_id = await self.client.register_dag_template_if_not_exists(
            project_id=self.project_id,
            dag_hash=dag_hash,
            code_hash=code_hash,
            name=self.dag_name,
            nodes=driver._extract_node_templates_from_function_graph(
                graph, include_result_builder=True
            ),
            code_artifacts=driver.extract_code_artifacts_from_function_graph(
                graph, vcs_info, vcs_info.local_repo_base_path
            ),
            config=graph.config,
            tags=self.base_tags,
            code=driver._slurp_code(graph, vcs_info.local_repo_base_path),
            vcs_info=vcs_info,
        )
        self.dag_template_id_cache[fg_id] = dag_template_id

    async def pre_graph_execute(
        self,
        run_id: str,
        graph: h_graph.FunctionGraph,
        final_vars: list[str],
        inputs: dict[str, Any],
        overrides: dict[str, Any],
    ):
        logger.debug("pre_graph_execute %s", run_id)
        fg_id = id(graph)
        if fg_id in self.dag_template_id_cache:
            dag_template_id = self.dag_template_id_cache[fg_id]
        else:
            raise ValueError("DAG template ID not found in cache. This should never happen.")

        tracking_state = TrackingState(run_id)
        self.tracking_states[run_id] = tracking_state  # cache
        tracking_state.clock_start()
        dw_run_id = await self.client.create_and_start_dag_run(
            dag_template_id=dag_template_id,
            tags=self.base_tags,
            inputs=inputs if inputs is not None else {},
            outputs=final_vars,
        )
        self.dw_run_ids[run_id] = dw_run_id
        self.task_runs[run_id] = {}
        self.final_vars[run_id] = final_vars

    async def pre_node_execute(
        self, run_id: str, node_: node.Node, kwargs: dict[str, Any], task_id: Optional[str] = None
    ):
        logger.debug("pre_node_execute %s", run_id)
        tracking_state = self.tracking_states[run_id]
        if tracking_state.status == Status.UNINITIALIZED:  # not thread safe?
            tracking_state.update_status(Status.RUNNING)

        task_run = TaskRun(node_name=node_.name)
        task_run.status = Status.RUNNING
        task_run.start_time = datetime.datetime.now(UTC)
        tracking_state.update_task(node_.name, task_run)
        self.task_runs[run_id][node_.name] = task_run

        task_update = dict(
            node_template_name=node_.name,
            node_name=get_node_name(node_, task_id),
            realized_dependencies=[dep.name for dep in node_.dependencies],
            status=task_run.status,
            start_time=task_run.start_time,
            end_time=None,
        )
        await self.client.update_tasks(
            self.dw_run_ids[run_id],
            attributes=[],
            task_updates=[task_update],
            in_samples=[task_run.is_in_sample],
        )

    async def post_node_execute(
        self,
        run_id: str,
        node_: node.Node,
        success: bool,
        error: Optional[Exception],
        result: Any,
        task_id: Optional[str] = None,
        **future_kwargs,
    ):
        logger.debug("post_node_execute %s", run_id)
        task_run = self.task_runs[run_id][node_.name]
        tracking_state = self.tracking_states[run_id]
        task_run.end_time = datetime.datetime.now(UTC)
        other_results = []

        if success:
            task_run.status = Status.SUCCESS
            task_run.result_type = type(result)
            result_summary, schema, additional = runs.process_result(result, node_)  # add node
            other_results = ([schema] if schema is not None else []) + additional
            if result_summary is None:
                result_summary = {
                    "observability_type": "observability_failure",
                    "observability_schema_version": "0.0.3",
                    "observability_value": {
                        "type": str(str),
                        "value": "Failed to process result.",
                    },
                }
            task_run.result_summary = result_summary
            task_attr = dict(
                node_name=get_node_name(node_, task_id),
                name="result_summary",
                type=task_run.result_summary["observability_type"],
                # 0.0.3 -> 3
                schema_version=int(
                    task_run.result_summary["observability_schema_version"].split(".")[-1]
                ),
                value=task_run.result_summary["observability_value"],
                attribute_role="result_summary",
            )
        else:
            task_run.status = Status.FAILURE
            if isinstance(error, dq_base.DataValidationError):
                task_run.error = runs.serialize_data_quality_error(error)
            else:
                task_run.error = traceback.format_exception(type(error), error, error.__traceback__)
            task_attr = dict(
                node_name=get_node_name(node_, task_id),
                name="stack_trace",
                type="error",
                schema_version=1,
                value={
                    "stack_trace": task_run.error,
                },
                attribute_role="error",
            )

        attributes = [task_attr]
        for i, other_result in enumerate(other_results):
            other_attr = dict(
                node_name=get_node_name(node_, task_id),
                name=other_result.get("name", f"Attribute {i + 1}"),  # retrieve name if specified
                type=other_result["observability_type"],
                # 0.0.3 -> 3
                schema_version=int(other_result["observability_schema_version"].split(".")[-1]),
                value=other_result["observability_value"],
                attribute_role="result_summary",
            )
            attributes.append(other_attr)
        tracking_state.update_task(get_node_name(node_, task_id), task_run)
        task_update = dict(
            node_template_name=node_.name,
            node_name=get_node_name(node_, task_id),
            realized_dependencies=[dep.name for dep in node_.dependencies],
            status=task_run.status,
            start_time=task_run.start_time,
            end_time=task_run.end_time,
        )
        await self.client.update_tasks(
            self.dw_run_ids[run_id],
            attributes=attributes,
            task_updates=[task_update for _ in attributes],
            in_samples=[task_run.is_in_sample for _ in attributes],
        )

    async def _emit_result_builder_task_run(
        self, run_id: str, results: Any, timestamp: datetime.datetime
    ):
        """Emits the task run for the synthetic ``_result_builder`` node.

        ``results`` here is always the raw output dict, never a built result:
        ``async_driver.execute()`` awaits ``raw_execute()`` -- whose ``finally`` fires this hook
        -- and only then calls ``do_build_result``, so the tracker cannot observe the builder.

        Failures are logged and swallowed, as in the sync tracker.
        """
        try:
            task_run, attributes, task_update = _result_builder_payload(
                results, timestamp, self.final_vars.get(run_id, [])
            )
            self.tracking_states[run_id].update_task(task_run.node_name, task_run)
            await self.client.update_tasks(
                self.dw_run_ids[run_id],
                attributes=attributes,
                task_updates=[task_update for _ in attributes],
                in_samples=[True for _ in attributes],
            )
        except Exception:
            logger.exception("Failed to emit the %s task run.", driver.RESULT_BUILDER_NODE_NAME)

    async def post_graph_execute(
        self,
        run_id: str,
        graph: h_graph.FunctionGraph,
        success: bool,
        error: Optional[Exception],
        results: Optional[dict[str, Any]],
    ):
        logger.debug("post_graph_execute %s", run_id)
        dw_run_id = self.dw_run_ids[run_id]
        tracking_state = self.tracking_states[run_id]
        tracking_state.clock_end(status=Status.SUCCESS if success else Status.FAILURE)
        finally_block_time = datetime.datetime.now(UTC)
        if tracking_state.status != Status.SUCCESS:
            # TODO: figure out how to handle crtl+c stuff
            tracking_state.status = Status.FAILURE
            # this assumes the task map only has things that have been processed, not
            # nodes that have yet to be computed.
            for task_name, task_run in tracking_state.task_map.items():
                if task_run.status != Status.SUCCESS:
                    task_run.status = Status.FAILURE
                    task_run.end_time = finally_block_time
                    if task_run.error is None:  # we likely aborted it.
                        # Note if we start to do concurrent execution we'll likely
                        # need to adjust this.
                        task_run.error = ["Run was likely aborted."]
                if task_run.end_time is None and task_run.status == Status.SUCCESS:
                    task_run.end_time = finally_block_time
        elif driver._should_register_result_builder(graph):
            await self._emit_result_builder_task_run(run_id, results, finally_block_time)

        # TODO: only update things that have changed?
        # self.client.update_tasks(
        #     dag_run_id=dw_run_id,
        #     attributes=driver.extract_attributes_from_tracking_state(tracking_state),
        #     task_updates=driver.extract_task_updates_from_tracking_state(tracking_state, graph),
        # )
        await self.client.log_dag_run_end(
            dag_run_id=dw_run_id,
            status=tracking_state.status.value,
        )
        logger.warning(
            f"\nCaptured execution run. Results can be found at "
            f"{self.hamilton_ui_url}/dashboard/project/{self.project_id}/runs/{dw_run_id}\n"
        )
