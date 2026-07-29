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
from collections.abc import Callable

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


def _failed_result_summary() -> dict:
    """Returns a fresh placeholder summary for results that could not be processed.

    A fresh dict each call -- callers assign it to per-run state, so a shared
    module-level constant would alias across runs.

    @return: An observability summary dict marking the result as unprocessable.
    """
    return {
        "observability_type": "observability_failure",
        "observability_schema_version": "0.0.3",
        "observability_value": {
            "type": str(str),
            "value": "Failed to process result.",
        },
    }


def _make_result_attributes(
    node_name: str, result_summary: dict | None, other_results: list[dict]
) -> list[dict]:
    """Shapes process_result output into update_tasks attributes.

    `result_summary` comes first because the order influences UI display order.

    @param node_name: Name of the node the attributes belong to.
    @param result_summary: Primary observability summary, or None if processing failed.
    @param other_results: Additional observability dicts (schema, extra attributes).
    @return: A list of attribute dicts for client.update_tasks.
    """
    if result_summary is None:
        result_summary = _failed_result_summary()
    attributes = [
        dict(
            node_name=node_name,
            name="result_summary",
            type=result_summary["observability_type"],
            # 0.0.3 -> 3
            schema_version=int(result_summary["observability_schema_version"].split(".")[-1]),
            value=result_summary["observability_value"],
            attribute_role="result_summary",
        )
    ]
    for i, other_result in enumerate(other_results):
        attributes.append(
            dict(
                node_name=node_name,
                name=other_result.get("name", f"Attribute {i + 1}"),  # retrieve name if specified
                type=other_result["observability_type"],
                # 0.0.3 -> 3
                schema_version=int(other_result["observability_schema_version"].split(".")[-1]),
                value=other_result["observability_value"],
                attribute_role="result_summary",
            )
        )
    return attributes


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
        self.result_builder_nodes = {}  # fg_id -> synthetic node (or None if no builder)
        self.run_final_vars = {}  # run_id -> final_vars, for realized_dependencies
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
        builder = driver._get_result_builder(graph)
        self.result_builder_nodes[fg_id] = (
            driver._create_result_builder_node(builder) if builder is not None else None
        )
        if fg_id in self.dag_template_id_cache:
            logger.warning("Skipping creation of DAG template as it already exists.")
            return
        module_hash = driver._get_modules_hash(modules)
        vcs_info = driver._derive_version_control_info(module_hash)
        dag_hash = driver.hash_dag(graph)
        code_hash = driver.hash_dag_modules(graph, modules)
        nodes = driver._extract_node_templates_from_function_graph(graph)
        if self.result_builder_nodes[fg_id] is not None:
            nodes.append(driver._extract_node_template(self.result_builder_nodes[fg_id]))
        dag_template_id = self.client.register_dag_template_if_not_exists(
            project_id=self.project_id,
            dag_hash=dag_hash,
            code_hash=code_hash,
            name=self.dag_name,
            nodes=nodes,
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
        self.run_final_vars[run_id] = list(final_vars)
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

        if success:
            task_run.status = Status.SUCCESS
            task_run.result_type = type(result)
            result_summary, schema, additional_attributes = runs.process_result(result, node_)
            if result_summary is None:
                result_summary = _failed_result_summary()
            other_results = ([schema] if schema is not None else []) + additional_attributes
            task_run.result_summary = result_summary
            # `result_summary` is first because the order influences UI display order
            attributes = _make_result_attributes(
                get_node_name(node_, task_id), result_summary, other_results
            )
        else:
            task_run.status = Status.FAILURE
            task_run.is_in_sample = True  # override any sampling
            if isinstance(error, dq_base.DataValidationError):
                task_run.error = runs.serialize_data_quality_error(error)
            else:
                task_run.error = traceback.format_exception(type(error), error, error.__traceback__)
            attributes = [
                dict(
                    node_name=get_node_name(node_, task_id),
                    name="stack_trace",
                    type="error",
                    schema_version=1,
                    value={
                        "stack_trace": task_run.error,
                    },
                    attribute_role="error",
                )
            ]
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

        builder_node = self.result_builder_nodes.get(id(graph))
        # `execute()` fires this hook after do_build_result, so `results` is the combined
        # built object. Deprecated raw_execute()/materialize() paths fire it with the raw
        # node dict without ever running the builder -- the type check skips those so we
        # don't report a builder execution that never happened.
        if (
            builder_node is not None
            and success
            and results is not None
            and (not isinstance(builder_node.type, type) or isinstance(results, builder_node.type))
        ):
            try:
                now = datetime.datetime.now(UTC)
                result_summary, schema, additional = runs.process_result(results, builder_node)
                attributes = _make_result_attributes(
                    builder_node.name,
                    result_summary,
                    ([schema] if schema is not None else []) + additional,
                )
                task_update = dict(
                    node_template_name=builder_node.name,
                    node_name=builder_node.name,  # no task_id at the graph level
                    realized_dependencies=self.run_final_vars.get(run_id, []),
                    status=Status.SUCCESS,
                    # builder duration is not observable from this hook
                    start_time=now,
                    end_time=now,
                )
                self.client.update_tasks(
                    dw_run_id,
                    attributes=attributes,
                    task_updates=[task_update for _ in attributes],
                    in_samples=[True for _ in attributes],
                )
            except Exception:
                # tracking must never fail the user's run
                logger.warning("Failed to track result builder output.", exc_info=True)

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
        self.result_builder_nodes = {}  # fg_id -> synthetic node (or None if no builder)
        self.run_final_vars = {}  # run_id -> final_vars, for realized_dependencies
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
        builder = driver._get_result_builder(graph)
        self.result_builder_nodes[fg_id] = (
            driver._create_result_builder_node(builder) if builder is not None else None
        )
        if fg_id in self.dag_template_id_cache:
            logger.warning("Skipping creation of DAG template as it already exists.")
            return
        module_hash = driver._get_modules_hash(modules)
        vcs_info = driver._derive_version_control_info(module_hash)
        dag_hash = driver.hash_dag(graph)
        code_hash = driver.hash_dag_modules(graph, modules)
        nodes = driver._extract_node_templates_from_function_graph(graph)
        if self.result_builder_nodes[fg_id] is not None:
            nodes.append(driver._extract_node_template(self.result_builder_nodes[fg_id]))
        dag_template_id = await self.client.register_dag_template_if_not_exists(
            project_id=self.project_id,
            dag_hash=dag_hash,
            code_hash=code_hash,
            name=self.dag_name,
            nodes=nodes,
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
        self.run_final_vars[run_id] = list(final_vars)

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

        if success:
            task_run.status = Status.SUCCESS
            task_run.result_type = type(result)
            result_summary, schema, additional = runs.process_result(result, node_)  # add node
            other_results = ([schema] if schema is not None else []) + additional
            if result_summary is None:
                result_summary = _failed_result_summary()
            task_run.result_summary = result_summary
            # `result_summary` is first because the order influences UI display order
            attributes = _make_result_attributes(
                get_node_name(node_, task_id), result_summary, other_results
            )
        else:
            task_run.status = Status.FAILURE
            if isinstance(error, dq_base.DataValidationError):
                task_run.error = runs.serialize_data_quality_error(error)
            else:
                task_run.error = traceback.format_exception(type(error), error, error.__traceback__)
            attributes = [
                dict(
                    node_name=get_node_name(node_, task_id),
                    name="stack_trace",
                    type="error",
                    schema_version=1,
                    value={
                        "stack_trace": task_run.error,
                    },
                    attribute_role="error",
                )
            ]
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

        builder_node = self.result_builder_nodes.get(id(graph))
        if builder_node is not None and success:
            # Unlike the sync driver, the async driver fires this hook *before*
            # do_build_result (async_driver.py raw_execute finally vs execute), so
            # `results` here is the raw dict -- emit a status-only update, no summary.
            try:
                now = datetime.datetime.now(UTC)
                task_update = dict(
                    node_template_name=builder_node.name,
                    node_name=builder_node.name,  # no task_id at the graph level
                    realized_dependencies=self.run_final_vars.get(run_id, []),
                    status=Status.SUCCESS,
                    # builder duration is not observable from this hook
                    start_time=now,
                    end_time=now,
                )
                await self.client.update_tasks(
                    dw_run_id,
                    attributes=[None],
                    task_updates=[task_update],
                    in_samples=[True],
                )
            except Exception:
                # tracking must never fail the user's run
                logger.warning("Failed to track result builder output.", exc_info=True)

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
