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

from typing import Any, Collection, List

import rich.progress

from hamilton.execution.grouping import NodeGroupPurpose

try:
    from typing import override
except ImportError:
    override = lambda x: x  # noqa E731

import rich
from rich.progress import Progress

from hamilton.lifecycle import (
    GraphExecutionHook,
    NodeExecutionHook,
    TaskExecutionHook,
    TaskGroupingHook,
)


class RichProgressBar(TaskExecutionHook, TaskGroupingHook, GraphExecutionHook, NodeExecutionHook):
    """An adapter that uses rich to show simple progress bars for the graph execution.

    Note: you need to have rich installed for this to work. If you don't have it installed, you can
    install it with `pip install rich` (or `pip install sf-hamilton[rich]` -- use quotes if you're
    using zsh).

    .. code-block:: python

        from hamilton import driver
        from hamilton.plugins import h_rich

        dr = (
            driver.Builder()
            .with_config({})
            .with_modules(some_modules)
            .with_adapters(h_rich.RichProgressBar())
            .build()
        )

    and then when you call .execute() or .materialize() you'll get a progress bar!

    Additionally, this progress bar will also work with task-based execution, showing the progress
    of overall execution as well as the tasks within a parallelized group.

    .. code-block:: python

        from hamilton import driver
        from hamilton.execution import executors
        from hamilton.plugins import h_rich

        dr = (
            driver.Builder()
            .with_modules(__main__)
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_adapters(RichProgressBar())
            .with_local_executor(executors.SynchronousLocalTaskExecutor())
            .with_remote_executor(executors.SynchronousLocalTaskExecutor())
            .build()
        )
    """

    def __init__(
        self,
        run_desc: str = "",
        collect_desc: str = "",
        columns: list[str | rich.progress.ProgressColumn] | None = None,
        **kwargs,
    ) -> None:
        """Create a new Rich Progress Bar adapter.

        :param run_desc: The description to show for the running phase.
        :param collect_desc: The description to show for the collecting phase (if applicable).
        :param columns: Column configuration for the progress bar.  See rich docs for more info.
        :param kwargs: Additional kwargs to pass to rich.progress.Progress. See rich docs for more info.
        """
        self._group_desc = run_desc if run_desc else "Running:"
        self._expand_desc = collect_desc if collect_desc else "Collecting:"
        columns = columns if columns else []
        self._progress = Progress(*columns, **kwargs)
        self._task_based = False

    @override
    def run_before_graph_execution(self, *, execution_path: Collection[str], **kwargs: Any):
        self._progress.add_task(self._group_desc, total=len(execution_path))
        self._progress.start()

    @override
    def run_after_graph_execution(self, **kwargs: Any):
        self._progress.stop()  # in case progress thread is lagging

    @override
    def run_after_task_grouping(self, *, task_ids: List[str], **kwargs):
        # Change the total of the task group to the number of tasks in the group
        self._progress.update(self._progress.task_ids[0], total=len(task_ids))
        self._task_based = True

    @override
    def run_after_task_expansion(self, *, parameters: dict[str, Any], **kwargs):
        self._progress.add_task(self._expand_desc, total=len(parameters))

    @override
    def run_before_task_execution(self, *, purpose: NodeGroupPurpose, **kwargs):
        if purpose == NodeGroupPurpose.GATHER:
            self._progress.advance(self._progress.task_ids[0])
            self._progress.stop_task(self._progress.task_ids[-1])

    @override
    def run_after_task_execution(self, *, purpose: NodeGroupPurpose, **kwargs):
        if purpose == NodeGroupPurpose.EXECUTE_BLOCK:
            self._progress.advance(self._progress.task_ids[-1])
        else:
            self._progress.advance(self._progress.task_ids[0])

    @override
    def run_before_node_execution(self, **kwargs):
        pass

    @override
    def run_after_node_execution(self, **kwargs):
        if not self._task_based:
            self._progress.advance(self._progress.task_ids[0])
