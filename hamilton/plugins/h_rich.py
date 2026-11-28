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
import threading
from collections.abc import Collection
from typing import Any

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


@dataclasses.dataclass
class _RunBars:
    task_ids: list[rich.progress.TaskID]
    task_based: bool = False
    finished: bool = False


class RichProgressBar(TaskExecutionHook, TaskGroupingHook, GraphExecutionHook, NodeExecutionHook):
    """An adapter that uses rich to show simple progress bars for the graph execution.

    Note: you need to have rich installed for this to work. If you don't have it installed, you can
    install it with `pip install rich` (or `pip install apache-hamilton[rich]` -- use quotes if you're
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
        self._group_desc = run_desc or "Running:"
        self._expand_desc = collect_desc or "Collecting:"
        columns = columns or []
        self._progress = Progress(*columns, **kwargs)
        self._runs: dict[str, _RunBars] = {}
        self._lock = threading.Lock()

    @override
    def run_before_graph_execution(
        self, *, run_id: str, execution_path: Collection[str], **kwargs: Any
    ):
        # the adapter outlives a run, so clear the bars of runs that have finished
        with self._lock:
            for finished in [r for r, bars in self._runs.items() if bars.finished]:
                for task_id in self._runs.pop(finished).task_ids:
                    self._progress.remove_task(task_id)
            group = self._progress.add_task(self._group_desc, total=len(execution_path))
            self._runs[run_id] = _RunBars([group])
            self._progress.start()

    @override
    def run_after_graph_execution(self, *, run_id: str, **kwargs: Any):
        with self._lock:
            if run_id in self._runs:
                self._runs[run_id].finished = True
            if all(bars.finished for bars in self._runs.values()):
                self._progress.stop()

    @override
    def run_after_task_grouping(self, *, run_id: str, task_ids: list[str], **kwargs):
        # Change the total of the task group to the number of tasks in the group
        bars = self._runs[run_id]
        self._progress.update(bars.task_ids[0], total=len(task_ids))
        bars.task_based = True

    @override
    def run_after_task_expansion(self, *, run_id: str, parameters: dict[str, Any], **kwargs):
        task_id = self._progress.add_task(self._expand_desc, total=len(parameters))
        self._runs[run_id].task_ids.append(task_id)

    @override
    def run_before_task_execution(self, *, run_id: str, purpose: NodeGroupPurpose, **kwargs):
        if purpose == NodeGroupPurpose.GATHER:
            task_ids = self._runs[run_id].task_ids
            self._progress.advance(task_ids[0])
            self._progress.stop_task(task_ids[-1])

    @override
    def run_after_task_execution(self, *, run_id: str, purpose: NodeGroupPurpose, **kwargs):
        task_ids = self._runs[run_id].task_ids
        if purpose == NodeGroupPurpose.EXECUTE_BLOCK:
            self._progress.advance(task_ids[-1])
        else:
            self._progress.advance(task_ids[0])

    @override
    def run_before_node_execution(self, **kwargs):
        pass

    @override
    def run_after_node_execution(self, *, run_id: str, **kwargs):
        bars = self._runs[run_id]
        if not bars.task_based:
            self._progress.advance(bars.task_ids[0])
