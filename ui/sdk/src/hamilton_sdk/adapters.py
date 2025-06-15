import datetime
import hashlib
import logging
import os
import random
import traceback
from datetime import timezone
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Union

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
        tags: Dict[str, str] = None,
        client_factory: Callable[
            [str, str, str, Union[str, bool]], clients.HamiltonClient
        ] = clients.BasicSynchronousHamiltonClient,
        api_key: str = None,
        hamilton_api_url=os.environ.get("HAMILTON_API_URL", constants.HAMILTON_API_URL),
        hamilton_ui_url=os.environ.get("HAMILTON_UI_URL", constants.HAMILTON_UI_URL),
        verify: Union[str, bool] = True,
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
        self, graph: h_graph.FunctionGraph, modules: List[ModuleType], config: Dict[str, Any]
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
        dag_hash = driver.hash_dag(graph)
        code_hash = driver.hash_dag_modules(graph, modules)
        dag_template_id = self.client.register_dag_template_if_not_exists(
            project_id=self.project_id,
            dag_hash=dag_hash,
            code_hash=code_hash,
            name=self.dag_name,
            nodes=driver._extract_node_templates_from_function_graph(graph),
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
        final_vars: List[str],
        inputs: Dict[str, Any],
        overrides: Dict[str, Any],
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
        logger.warning(
            f"\nCapturing execution run. Results can be found at "
            f"{self.hamilton_ui_url}/dashboard/project/{self.project_id}/runs/{dw_run_id}\n"
        )
        return dw_run_id

    def pre_node_execute(
        self, run_id: str, node_: node.Node, kwargs: Dict[str, Any], task_id: Optional[str] = None
    ):
        """Captures start of node execution."""
        logger.debug("pre_node_execute %s %s", run_id, task_id)
        tracking_state = self.tracking_states[run_id]
        if tracking_state.status == Status.UNINITIALIZED:  # not thread safe?
            tracking_state.update_status(Status.RUNNING)

        in_sample = self.is_in_sample(task_id)
        task_run = TaskRun(node_name=node_.name, is_in_sample=in_sample)
        task_run.status = Status.RUNNING
        task_run.start_time = datetime.datetime.now(timezone.utc)
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
        kwargs: Dict[str, Any],
        success: bool,
        error: Optional[Exception],
        result: Optional[Any],
        task_id: Optional[str] = None,
    ):
        """Captures end of node execution."""
        logger.debug("post_node_execute %s %s", run_id, task_id)
        task_run: TaskRun = self.task_runs[run_id][node_.name]
        tracking_state = self.tracking_states[run_id]
        task_run.end_time = datetime.datetime.now(timezone.utc)

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

    def post_graph_execute(
        self,
        run_id: str,
        graph: h_graph.FunctionGraph,
        success: bool,
        error: Optional[Exception],
        results: Optional[Dict[str, Any]],
    ):
        """Captures end of DAG execution."""
        logger.debug("post_graph_execute %s", run_id)
        dw_run_id = self.dw_run_ids[run_id]
        tracking_state = self.tracking_states[run_id]
        tracking_state.clock_end(status=Status.SUCCESS if success else Status.FAILURE)
        finally_block_time = datetime.datetime.utcnow()
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
        tags: Dict[str, str] = None,
        client_factory: Callable[
            [str, str, str, Union[str, bool]], clients.BasicAsynchronousHamiltonClient
        ] = clients.BasicAsynchronousHamiltonClient,
        api_key: str = os.environ.get("HAMILTON_API_KEY", ""),
        hamilton_api_url=os.environ.get("HAMILTON_API_URL", constants.HAMILTON_API_URL),
        hamilton_ui_url=os.environ.get("HAMILTON_UI_URL", constants.HAMILTON_UI_URL),
        verify: Union[str, bool] = True,
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
        self, graph: h_graph.FunctionGraph, modules: List[ModuleType], config: Dict[str, Any]
    ):
        logger.debug("post_graph_construct")
        fg_id = id(graph)
        if fg_id in self.dag_template_id_cache:
            logger.warning("Skipping creation of DAG template as it already exists.")
            return
        module_hash = driver._get_modules_hash(modules)
        vcs_info = driver._derive_version_control_info(module_hash)
        dag_hash = driver.hash_dag(graph)
        code_hash = driver.hash_dag_modules(graph, modules)
        dag_template_id = await self.client.register_dag_template_if_not_exists(
            project_id=self.project_id,
            dag_hash=dag_hash,
            code_hash=code_hash,
            name=self.dag_name,
            nodes=driver._extract_node_templates_from_function_graph(graph),
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
        final_vars: List[str],
        inputs: Dict[str, Any],
        overrides: Dict[str, Any],
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

    async def pre_node_execute(
        self, run_id: str, node_: node.Node, kwargs: Dict[str, Any], task_id: Optional[str] = None
    ):
        logger.debug("pre_node_execute %s", run_id)
        tracking_state = self.tracking_states[run_id]
        if tracking_state.status == Status.UNINITIALIZED:  # not thread safe?
            tracking_state.update_status(Status.RUNNING)

        task_run = TaskRun(node_name=node_.name)
        task_run.status = Status.RUNNING
        task_run.start_time = datetime.datetime.now(timezone.utc)
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
        task_run.end_time = datetime.datetime.now(timezone.utc)
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

    async def post_graph_execute(
        self,
        run_id: str,
        graph: h_graph.FunctionGraph,
        success: bool,
        error: Optional[Exception],
        results: Optional[Dict[str, Any]],
    ):
        logger.debug("post_graph_execute %s", run_id)
        dw_run_id = self.dw_run_ids[run_id]
        tracking_state = self.tracking_states[run_id]
        tracking_state.clock_end(status=Status.SUCCESS if success else Status.FAILURE)
        finally_block_time = datetime.datetime.utcnow()
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
