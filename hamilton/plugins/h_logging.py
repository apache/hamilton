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

"""Synchronous/asynchronous adapter and functions for context-aware logging with Hamilton."""

import logging
import sys
from contextvars import ContextVar
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Set,
    Tuple,
    Union,
)

from hamilton.graph_types import HamiltonNode
from hamilton.lifecycle.api import (
    GraphExecutionHook,
    NodeExecutionHook,
    TaskExecutionHook,
    TaskGroupingHook,
    TaskReturnHook,
    TaskSubmissionHook,
)
from hamilton.lifecycle.base import BasePostNodeExecuteAsync, BasePreNodeExecute
from hamilton.node import Node

try:
    from typing import override
except ImportError:
    override = lambda x: x  # noqa E731


if sys.version_info >= (3, 12):
    LoggerAdapter = logging.LoggerAdapter[logging.Logger]
else:
    if TYPE_CHECKING:
        LoggerAdapter = logging.LoggerAdapter[logging.Logger]
    else:
        LoggerAdapter = logging.LoggerAdapter


@dataclass(frozen=True)
class _LoggingContext:
    """Represents the current logging context."""

    graph: Optional[str] = None
    node: Optional[str] = None
    task: Optional[str] = None


# Context variables for context-aware logging
_local_context = ContextVar("context", default=_LoggingContext())


def get_logger(name: Optional[str] = None) -> "ContextLogger":
    """Returns a context-aware logger for the specified name (created if necessary).

    :param name: Name of the logger, defaults to root logger if not provided.
    """
    logger = logging.getLogger(name)
    return ContextLogger(logger, extra={})


class ContextLogger(LoggerAdapter):
    """Custom logger adapter for Hamilton that adds context to log messages.

    This logger adds context-aware prefix to log messages based on the current execution. The
    logger is intended to be used with hamilton the `LoggingAdapter` lifecycle adapter. The context
    is both thread-safe and async-safe. Context includes the following details:
    - Graph run
    - Task ID
    - Node ID

    The adapter also supports the following extra fields:
    - `override_context`: Overrides the current context with the specified context.
    - `skip_context`: Skips the context for the current log message.
    - `node_context`: Includes additional node information for task-based log messages.
    """

    @override
    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> Tuple[str, MutableMapping[str, Any]]:
        # Ensure that the extra fields are passed through correctly
        kwargs["extra"] = {**(self.extra or {}), **(kwargs.get("extra") or {})}

        # Add the current prefix to the log message
        prefix = self._get_current_context(kwargs["extra"])
        msg = f"{prefix}{msg}"

        return (msg, kwargs)

    def _get_current_context(self, extra: Mapping[str, Any]) -> str:
        """Returns the current context."""

        # Extra option to override context
        context = extra.get("override_context", None)
        if not isinstance(context, _LoggingContext):
            context = _local_context.get()

        # Extra option to skip context
        if "skip_context" in extra:
            return ""

        if context.task:
            # Extra option to include node information on task-based log messages
            if context.node and "node_context" in extra:
                return f"Task '{context.task}' - Node '{context.node}' - "
            return f"Task '{context.task}' - "

        if context.node:
            return f"Node '{context.node}' - "

        if context.graph:
            return f"Graph run '{context.graph}' - "

        return ""


class LoggingAdapter(
    GraphExecutionHook,
    NodeExecutionHook,
    TaskGroupingHook,
    TaskSubmissionHook,
    TaskExecutionHook,
    TaskReturnHook,
):
    """Hamilton lifecycle adapter that logs runtime execution events.

    This adapter logs the following hamilton events:
    - Graph start (`GraphExecutionHook`)
    - Task grouping (`TaskGroupingHook`)
    - Task submission (`TaskSubmissionHook`)
    - Task pre-execution (`TaskExecutionHook`))
    - Node pre-execution (`NodeExecutionHook`)
    - Node post-execution (`NodeExecutionHook`)
    - Task post-execution (`TaskExecutionHook`))
    - Task resolution  (`TaskReturnHook`)
    - Graph completion  (`GraphExecutionHook`)

    This adapter can be run with both node-based and task-based execution (using the V2 executor).
    When run with a node-based executor, the adapter logs the execution of each *node* as `INFO`.
    When run with a task-based executor, the adapter logs the execution of each *task* as `INFO`
    and the execution of each *node* as `DEBUG`.
    """

    def __init__(self, logger: Union[str, logging.Logger, None] = None) -> None:
        # Precompute or overridden nodes
        self._inputs_nodes: Set[str] = set()
        self._override_nodes: Set[str] = set()

        if logger is None:
            self.logger = logging.getLogger(__name__)
        elif isinstance(logger, logging.Logger):
            self.logger = logger
        else:
            self.logger = logging.getLogger(logger)

        if not isinstance(self.logger, ContextLogger):
            self.logger = ContextLogger(self.logger, extra={})

        self._exception_logged = False  # For tracking remote exceptions

    @override
    def run_before_graph_execution(
        self,
        *,
        inputs: Optional[Dict[str, Any]],
        overrides: Optional[Dict[str, Any]],
        run_id: str,
        **future_kwargs: Any,
    ):
        # Set context before logging
        _local_context.set(_LoggingContext(graph=run_id))

        self._inputs_nodes.update(inputs or [])
        self._override_nodes.update(overrides or [])

        message = "Starting graph execution"
        self.logger.info(message)

        if inputs:
            names = ", ".join(f"'{key}'" for key in inputs)
            self.logger.info("Using inputs %s", names)

        if overrides:
            names = ", ".join(f"'{key}'" for key in overrides)
            self.logger.info("Using overrides %s", names)

    @override
    def run_after_task_grouping(self, *, run_id: str, task_ids: List[str], **future_kwargs):
        self.logger.info("Dynamic DAG detected; task-based logging is enabled")

    @override
    def run_after_task_expansion(self, **future_kwargs):
        pass  # Note currently uses; required for TaskGroupingHook

    @override
    def run_before_task_submission(
        self,
        *,
        run_id: str,
        task_id: str,
        spawning_task_id: Optional[str],
        **future_kwargs,
    ):
        # Set context before logging
        _local_context.set(_LoggingContext(graph=run_id, task=task_id))

        if spawning_task_id:
            self.logger.debug("Spawning task and submitting to executor")
        else:
            self.logger.debug("Initializing new task and submitting to executor")

    @override
    def run_before_task_execution(
        self,
        *,
        task_id: str,
        run_id: str,
        nodes: List[HamiltonNode],
        **future_kwargs,
    ):
        # Set context before logging
        _local_context.set(_LoggingContext(graph=run_id, task=task_id))

        # Do not log if the task matches the inputs or overrides
        if task_id in self._inputs_nodes or task_id in self._override_nodes:
            return

        message = "Starting execution"
        if len(nodes) == 1 and nodes[0].name == task_id:  # single node task
            self.logger.debug(message)
        else:
            message += " of nodes %s"
            names = ", ".join(f"'{node.name}'" for node in nodes)
            self.logger.debug(message, names)

    @override
    def run_before_node_execution(
        self,
        *,
        node_name: str,
        node_kwargs: Dict[str, Any],
        task_id: Optional[str],
        run_id: str,
        **future_kwargs: Any,
    ):
        # Set context before logging
        _local_context.set(_LoggingContext(graph=run_id, task=task_id, node=node_name))

        message = "Starting execution"
        extra = {"include_task_node": True}
        if node_kwargs:
            message += " with dependencies %s"
            params = ", ".join(f"'{key}'" for key in node_kwargs)
            self.logger.debug(message, params, extra=extra)
        else:
            message += " without dependencies"
            self.logger.debug(message, extra=extra)

    @override
    def run_after_node_execution(
        self,
        *,
        node_name: str,
        error: Optional[Exception],
        success: bool,
        task_id: Optional[str],
        run_id: str,
        **future_kwargs: Any,
    ):
        # Reset context before logging via the token
        _local_context.set(_LoggingContext(graph=run_id, task=task_id))

        # Logger should use previous context and include node information for this method
        extra = {
            "override_context": _LoggingContext(graph=run_id, task=task_id, node=node_name),
            "node_context": True,
        }

        if success:
            log_func = self.logger.debug if task_id else self.logger.info
            log_func("Finished execution [OK]", extra=extra)
        elif error:
            self.logger.exception("Encountered error", extra=extra)
            self._exception_logged = True

    @override
    def run_after_task_execution(
        self,
        *,
        task_id: str,
        run_id: str,
        success: bool,
        error: Exception,
        **future_kwargs,
    ):
        # Reset context before logging
        _local_context.set(_LoggingContext(graph=run_id))

        # Logger should use previous context for this method
        extra = {"override_context": _LoggingContext(graph=run_id, task=task_id)}

        # Do not log if the task matches the inputs or overrides
        if task_id in self._inputs_nodes or task_id in self._override_nodes:
            return

        if success:
            self.logger.debug("Finished execution [OK]", extra=extra)
        elif error:
            self.logger.error("Execution failed due to errors", extra=extra)

    @override
    def run_after_task_return(
        self,
        *,
        run_id: str,
        task_id: str,
        nodes: List[Node],
        success: bool,
        error: Optional[Exception],
        **future_kwargs,
    ):
        # Hard reset context before logging
        _local_context.set(_LoggingContext(graph=run_id))

        # Logger should use previous context for this method
        extra = {"override_context": _LoggingContext(graph=run_id, task=task_id)}

        if success:
            # Input and override tasks should be logged as debug
            if task_id in self._inputs_nodes or task_id in self._override_nodes:
                log_func = self.logger.debug
            else:
                log_func = self.logger.info
            log_func("Task completed [OK]", extra=extra)
        elif error and not self._exception_logged:
            # NOTE: _exception_logged is used to prevent duplicate exception logging
            self.logger.exception("Task completion failed due to errors", extra=extra)
            self._exception_logged = True

    @override
    def run_after_graph_execution(
        self,
        *,
        success: bool,
        run_id: str,
        **future_kwargs: Any,
    ):
        # Hard reset context before logging
        _local_context.set(_LoggingContext())

        # Logger should use previous context for this method
        extra = {"override_context": _LoggingContext(graph=run_id)}

        if success:
            self.logger.info("Finished graph execution [OK]", extra=extra)
        else:
            self.logger.error("Graph execution failed due to errors", extra=extra)


class AsyncLoggingAdapter(GraphExecutionHook, BasePreNodeExecute, BasePostNodeExecuteAsync):
    """Async version of the `LoggingAdapter`.

    This adapter logs the following hamilton events:
    - Graph start (`GraphExecutionHook`)
    - Node pre-execution (`BasePreNodeExecute`)
    - Node post-execution (`BasePostNodeExecuteAsync`)
    - Graph completion  (`GraphExecutionHook`)

    Note that this adapter is intended to be used with the async driver. Due to current limitations
    with the async driver, this adapter is only able to approximate when the async node has been
    submitted. It cannot currently log the exact moment the async node begins execution.
    """

    def __init__(self, logger: Union[str, logging.Logger, None] = None) -> None:
        self._impl = LoggingAdapter(logger)

    @override
    def run_before_graph_execution(
        self,
        *,
        inputs: Dict[str, Any],
        overrides: Dict[str, Any],
        run_id: str,
        **future_kwargs: Any,
    ):
        self._impl.run_before_graph_execution(inputs=inputs, overrides=overrides, run_id=run_id)

    @override
    def pre_node_execute(
        self, *, run_id: str, node_: Node, kwargs: Dict[str, Any], task_id: Optional[str] = None
    ):
        # NOTE: We call the base synchronous method here in order to approximate when the async task
        # has bee submitted. This is a workaround until further work is done on the async adapter.

        # Set context before logging
        _local_context.set(_LoggingContext(graph=run_id, task=None, node=node_.name))

        message = "Submitting async node"
        extra = {"include_task_node": True}
        if kwargs:
            message += " with dependencies %s"
            params = ", ".join(f"'{key}'" for key in kwargs)
            self._impl.logger.debug(message, params, extra=extra)
        else:
            message += " without dependencies"
            self._impl.logger.debug(message, extra=extra)

    @override
    async def post_node_execute(
        self,
        *,
        run_id: str,
        node_: Node,
        kwargs: Dict[str, Any],
        success: bool,
        error: Optional[Exception],
        result: Any,
        task_id: Optional[str] = None,
    ):
        self._impl.run_after_node_execution(
            node_name=node_.name,
            error=error,
            success=success,
            task_id=task_id,
            run_id=run_id,
        )

    @override
    def run_after_graph_execution(
        self,
        *,
        success: bool,
        run_id: str,
        **future_kwargs: Any,
    ):
        self._impl.run_after_graph_execution(success=success, run_id=run_id)
