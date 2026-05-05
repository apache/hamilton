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

from hamilton import ad_hoc_utils, driver
from hamilton.plugins.h_tqdm import ProgressBar


def _build_driver(progress_bar: ProgressBar, module_name: str) -> driver.Driver:
    def normalized(raw_value: float) -> float:
        return raw_value / 100.0

    def scaled(normalized: float) -> float:
        return normalized * 10.0

    def total(scaled: float) -> float:
        return scaled + 5.0

    module = ad_hoc_utils.create_temporary_module(
        normalized, scaled, total, module_name=module_name
    )
    return driver.Builder().with_adapters(progress_bar).with_modules(module).build()


def test_progress_bar_reaches_total_with_overrides():
    """Regression test for #845: bar must hit 100% when overrides are passed."""
    progress_bar = ProgressBar()
    dr = _build_driver(progress_bar, "tqdm_pipeline_overrides")

    dr.execute(
        ["total"],
        overrides={"scaled": 42.0},
        inputs={"raw_value": 200.0},
    )

    assert progress_bar.progress_bar.n == progress_bar.progress_bar.total


def test_progress_bar_reaches_total_without_overrides():
    """Bar reaches 100% on a normal successful run."""
    progress_bar = ProgressBar()
    dr = _build_driver(progress_bar, "tqdm_pipeline_no_overrides")

    dr.execute(["total"], inputs={"raw_value": 200.0})

    assert progress_bar.progress_bar.n == progress_bar.progress_bar.total


def test_progress_bar_does_not_force_completion_on_failure():
    """Bar must not be forced to total when execution fails."""

    def step_one(raw_value: float) -> float:
        return raw_value

    def step_two(step_one: float) -> float:
        raise RuntimeError("boom")

    def step_three(step_two: float) -> float:
        return step_two

    module = ad_hoc_utils.create_temporary_module(
        step_one, step_two, step_three, module_name="tqdm_pipeline_failure"
    )
    progress_bar = ProgressBar()
    dr = driver.Builder().with_adapters(progress_bar).with_modules(module).build()

    try:
        dr.execute(["step_three"], inputs={"raw_value": 1.0})
    except Exception:
        pass

    assert progress_bar.progress_bar.n < progress_bar.progress_bar.total
