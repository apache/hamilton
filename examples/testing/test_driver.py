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

"""Integration tests that exercise the full DAG via the Driver.

These show three patterns:

1. Build a Driver from one or more modules and assert on its outputs.
2. Use ``inputs=`` to inject test data at the DAG inputs.
3. Use ``overrides=`` to short-circuit an intermediate node, so you can test
   downstream logic in isolation without recomputing upstream nodes.
"""

import my_functions
import pandas as pd

from hamilton import driver


def _build_driver() -> driver.Driver:
    """Helper: construct a Driver pointed at our module under test."""
    return driver.Builder().with_modules(my_functions).build()


def test_driver_executes_full_pipeline() -> None:
    dr = _build_driver()
    inputs = {
        "raw_signups": pd.Series([0, 1, 10, 50, 100, 200, 400]),
        "raw_spend": pd.Series([0, 10, 10, 20, 40, 40, 50]),
    }

    result = dr.execute(["spend_per_signup", "spend_mean"], inputs=inputs)

    # spend after dropping the header row: [10, 10, 20, 40, 40, 50] -> mean 28.333...
    assert result["spend_mean"] == pd.Series([10, 10, 20, 40, 40, 50]).mean()
    pd.testing.assert_series_equal(
        result["spend_per_signup"],
        pd.Series([10.0, 1.0, 0.4, 0.4, 0.2, 0.125]),
        check_names=False,
    )


def test_overrides_short_circuit_upstream_nodes() -> None:
    """`overrides=` lets us pin a node's value, so upstream code is skipped.

    This is the integration-test sweet spot: instead of fabricating realistic
    raw inputs and re-deriving every intermediate, we hand the DAG a known
    `spend` and assert on the *downstream* arithmetic.
    """
    dr = _build_driver()

    result = dr.execute(
        ["spend_zero_mean_unit_variance"],
        # No `inputs=` needed because every upstream dependency is overridden.
        overrides={"spend": pd.Series([10.0, 20.0, 30.0])},
    )

    scaled = result["spend_zero_mean_unit_variance"]
    # Standardised series: mean ~0, std ~1.
    assert abs(scaled.mean()) < 1e-9
    assert abs(scaled.std(ddof=1) - 1.0) < 1e-9


def test_what_is_upstream_of() -> None:
    """The Driver itself can be inspected -- handy for asserting graph shape."""
    dr = _build_driver()

    upstream_node_names = {n.name for n in dr.what_is_upstream_of("spend_per_signup")}

    # `spend_per_signup` depends (transitively) on the raw inputs and on `spend`/`signups`.
    assert {"spend", "signups", "raw_spend", "raw_signups"} <= upstream_node_names
