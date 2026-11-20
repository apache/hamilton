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
