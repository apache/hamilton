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
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest import mock

import pytest

from hamilton import ad_hoc_utils, driver

pytest.importorskip("rich")

from hamilton.plugins.h_rich import RichProgressBar  # noqa: E402


def _build_driver(progress_bar: RichProgressBar) -> driver.Driver:
    def normalized(raw_value: float) -> float:
        return raw_value / 100.0

    def total(normalized: float) -> float:
        return normalized + 5.0

    module = ad_hoc_utils.create_temporary_module(normalized, total)
    return driver.Builder().with_adapters(progress_bar).with_modules(module).build()


def test_progress_bar_reaches_total():
    progress_bar = RichProgressBar(disable=True)
    dr = _build_driver(progress_bar)

    dr.execute(["total"], inputs={"raw_value": 200.0})

    (task,) = progress_bar._progress.tasks
    assert task.completed == task.total == 2


def test_progress_bar_starts_fresh_on_each_execution():
    """Reusing the driver must show one bar per run, not stack a new empty bar on the old one."""
    progress_bar = RichProgressBar(disable=True)
    dr = _build_driver(progress_bar)

    dr.execute(["total"], inputs={"raw_value": 200.0})
    dr.execute(["total"], inputs={"raw_value": 300.0})

    (task,) = progress_bar._progress.tasks
    assert task.completed == task.total == 2


def test_overlapping_runs_keep_their_own_bars():
    progress_bar = RichProgressBar(disable=True)

    with mock.patch.object(progress_bar._progress, "stop") as stop:
        progress_bar.run_before_graph_execution(run_id="a", execution_path=["x", "y"])
        progress_bar.run_before_graph_execution(run_id="b", execution_path=["x"])
        progress_bar.run_after_node_execution(run_id="a")
        progress_bar.run_after_node_execution(run_id="b")
        progress_bar.run_after_graph_execution(run_id="b")
        stop.assert_not_called()

        progress_bar.run_after_node_execution(run_id="a")
        progress_bar.run_after_graph_execution(run_id="a")
        stop.assert_called_once()

    bars = sorted((task.completed, task.total) for task in progress_bar._progress.tasks)
    assert bars == [(1, 1), (2, 2)]


def test_concurrent_executions_of_one_driver():
    both_running = threading.Barrier(2, timeout=10)

    def raw(raw_value: float) -> float:
        both_running.wait()
        return raw_value

    def total(raw: float) -> float:
        return raw + 5.0

    progress_bar = RichProgressBar(disable=True)
    module = ad_hoc_utils.create_temporary_module(raw, total)
    dr = driver.Builder().with_adapters(progress_bar).with_modules(module).build()

    with ThreadPoolExecutor(max_workers=2) as pool:
        runs = [pool.submit(dr.execute, ["total"], inputs={"raw_value": v}) for v in (1.0, 2.0)]
        results = sorted(run.result()["total"] for run in runs)

    assert results == [6.0, 7.0]
    bars = [(task.completed, task.total) for task in progress_bar._progress.tasks]
    assert bars == [(2, 2), (2, 2)]
