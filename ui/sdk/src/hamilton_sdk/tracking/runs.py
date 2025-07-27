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
import importlib
import logging
import sys
import time as py_time
import traceback
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from hamilton_sdk.tracking import constants, data_observation
from hamilton_sdk.tracking.data_observation import ObservationType
from hamilton_sdk.tracking.trackingtypes import DAGRun, Status, TaskRun

from hamilton import node as h_node
from hamilton.data_quality import base as dq_base
from hamilton.lifecycle import base as lifecycle_base

_modules_to_import = [
    "numpy",
    "pandas",
    "polars",
    "pyspark",
    "ibis",
    "langchain",
    "pydantic",
    "scikit_learn",
]

logger = logging.getLogger(__name__)

for module in _modules_to_import:
    try:
        importlib.import_module(f"hamilton_sdk.tracking.{module}_stats")
    except ImportError:
        logger.debug(f"Failed to import hamilton_sdk.tracking.{module}_stats")
        pass


def process_result(
    result: Any, node: h_node.Node
) -> Tuple[Optional[ObservationType], Optional[ObservationType], List[ObservationType]]:
    """Processes result -- this is purely a by-type mapping.
    Note that this doesn't actually do anything yet -- the idea is that we can return DQ
    results, and do other stuff with other results -- E.G. summary stats on dataframes,
    pass small strings through, etc...

    The return type is left as Any for now, but we should probably make it a union of
    types that we support.

    Note this should keep the cardinality of the output as low as possible.
    These results will be used on the FE to display results, and we don't want
    to crowd out storage.

    :param result: The result of the node's execution
    :param node: The node that produced the result
    :return: The processed  result - it has to be JSON serializable!
    """
    statistics = None
    schema = None
    additional = []
    if constants.CAPTURE_DATA_STATISTICS:
        try:
            start = py_time.time()
            statistics = data_observation.compute_stats(result, node.name, node.tags)
            end = py_time.time()
            logger.debug(f"Took {end - start} seconds to describe {node.name}")
        except Exception as e:
            logger.warning(f"Failed to introspect statistics for {node.name}. Error:\n{e}")
    else:
        # TODO: handle case where it's metadata from a dataloader/saver right now we don't log that
        # info, but we should in this particular case.
        statistics = {
            "observability_type": "primitive",
            "observability_value": {
                "type": "str",
                "value": "RESULT SUMMARY DISABLED",
            },
            "observability_schema_version": "0.0.1",
        }
    try:
        start = py_time.time()
        schema = data_observation.compute_schema(result, node.name, node.tags)
        end = py_time.time()
        logger.debug(f"Took {end - start} seconds to introspect schema for {node.name}")
    except Exception as e:
        logger.warning(f"Failed to introspect schema for {node.name}. Error:\n{e}")
    try:
        start = py_time.time()
        additional.extend(data_observation.compute_additional_results(result, node.name, node.tags))
        end = py_time.time()
        logger.debug(f"Took {end - start} seconds to introspect additional results for {node.name}")
    except Exception as e:
        logger.warning(f"Failed to introspect additional results for {node.name}. Error:\n{e}")
    return statistics, schema, additional


class TrackingState:
    """Mutable class that tracks data"""

    def __init__(self, run_id: str):
        """Initializes the tracking state"""
        self.status = Status.UNINITIALIZED
        self.start_time = None
        self.end_time = None
        self.run_id = run_id
        self.task_map: Dict[str, TaskRun] = {}
        self.update_status(Status.UNINITIALIZED)

    def clock_start(self):
        """Called at start of run"""
        logger.info("Clocked beginning of run")
        self.status = Status.RUNNING
        self.start_time = datetime.now(timezone.utc)

    def clock_end(self, status: Status):
        """Called at end of run"""
        logger.info(f"Clocked end of run with status: {status}")
        self.end_time = datetime.now(timezone.utc)
        self.status = status

    def update_task(self, task_name: str, task_run: TaskRun):
        """Updates a task"""
        self.task_map.update({task_name: task_run})
        logger.debug(f"Updating task: {task_name} with data: {task_run}")

    def update_status(self, status: Status):
        """Updates the status of the run"""
        self.status = status
        logger.info(f"Updating run status with value: {status}")

    def get(self) -> DAGRun:
        """Gives the final result as a DAG run"""
        return DAGRun(
            run_id=self.run_id,
            status=self.status,
            # TODO -- think about using a json dumper and referring to this as a status
            tasks=list(self.task_map.values()),
            start_time=self.start_time,
            end_time=self.end_time,
            schema_version=0,
        )


def serialize_error() -> List[str]:
    """Serialize an error to a string.
    Note we should probably have this *unparsed*, so we can display in the UI,
    but its OK for now to just have the string.

    *note* this has to be called from within an except block.

    :param error:
    :return:
    """
    exc_type, exc_value, exc_tb = sys.exc_info()
    return traceback.format_exception(exc_type, exc_value, exc_tb)


def serialize_data_quality_error(e: dq_base.DataValidationError) -> List[str]:
    """Santizes data quality errors to make them more readable for the platform.

    Note: this is hacky code.

    :param e: Data quality error to inspect
    :return: list of failures.
    """
    validation_failures = e.args[0]
    sanitized_failures = []
    for failure in validation_failures:
        if "pandera_schema_validator" in failure:  # hack to know what type of validator.
            sanitized_failures.append(failure.split("Usage Tip")[0])  # remove usage tip
        else:
            sanitized_failures.append(failure)
    return sanitized_failures


class RunTracker:
    """This class allows you to track results of runs"""

    def __init__(self, tracking_state: TrackingState):
        """Tracks runs given run IDs. Note that this needs to be re-initialized
        on each run, we'll want to fix that.

        :param result_builder: Result builder to use
        :param run_id: Run ID to save with
        """
        self.tracking_state = tracking_state

    def execute_node(
        self,
        original_do_node_execute: Callable,
        run_id: str,
        node_: h_node.Node,
        kwargs: Dict[str, Any],
        task_id: Optional[str],
    ) -> Any:
        """Given a node that represents a hamilton function, execute it.
        Note, in some adapters this might just return some type of "future".

        :param node_: the Hamilton Node
        :param kwargs: the kwargs required to exercise the node function.
        :return: the result of exercising the node.
        :param original_execute_node: The original adapter's callable
        """
        logger.debug(f"Executing node: {node_.name}")
        # If the hamilton_tracking state hasn't started
        if self.tracking_state.status == Status.UNINITIALIZED:
            self.tracking_state.update_status(Status.RUNNING)

        task_run = TaskRun(node_name=node_.name)  # node run.
        task_run.status = Status.RUNNING
        task_run.start_time = datetime.now(timezone.utc)
        self.tracking_state.update_task(node_.name, task_run)
        try:
            result = original_do_node_execute(run_id, node_, kwargs, task_id)

            # In subsequent versions we will stop supporting the class-based approach
            # If you find yourself relying on this, switch to use adapters
            result_summary, *ignored_because_this_is_a_defunct_code_path = process_result(
                result, node_
            )  # add node
            task_run.status = Status.SUCCESS
            task_run.result_type = type(result)
            task_run.result_summary = result_summary
            task_run.end_time = datetime.now(timezone.utc)
            self.tracking_state.update_task(node_.name, task_run)
            logger.debug(f"Node: {node_.name} ran successfully")
            return result
        except dq_base.DataValidationError as e:
            task_run.status = Status.FAILURE
            task_run.end_time = datetime.now(timezone.utc)
            task_run.error = serialize_data_quality_error(e)
            self.tracking_state.update_status(Status.FAILURE)
            self.tracking_state.update_task(node_.name, task_run)
            logger.debug(f"Node: {node_.name} encountered data quality issue...")
            raise e
        except Exception as e:
            task_run.status = Status.FAILURE
            task_run.end_time = datetime.now(timezone.utc)
            task_run.error = serialize_error()
            self.tracking_state.update_status(Status.FAILURE)
            self.tracking_state.update_task(node_.name, task_run)
            logger.debug(f"Node: {node_.name} failed to run...")
            raise e


@contextmanager
def monkey_patch_adapter(
    adapter: lifecycle_base.LifecycleAdapterSet, tracking_state: TrackingState
):
    """Monkey patches the graph adapter to track the results o fthe run

    :param adapter: Adapter to modify the execute_node functionality
    :param tracking_state: State of the DAG -- used for tracking
    """

    (adapter_to_patch,) = [
        item for item in adapter.adapters if hasattr(item, "do_node_execute")
    ]  # Have to patch it
    original_do_node_execute = adapter_to_patch.do_node_execute
    try:
        run_tracker = RunTracker(tracking_state=tracking_state)
        # monkey patch the adapter
        adapter_to_patch.do_node_execute = functools.partial(
            run_tracker.execute_node, original_do_node_execute=original_do_node_execute
        )
        yield
    finally:
        adapter_to_patch.do_node_execute = original_do_node_execute
