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

"""Unit tests for the plain (un-decorated) Hamilton functions.

The point of these tests: a Hamilton function is just a Python function. You
can import it and call it directly -- no Driver, no DAG, no fixtures required.
"""

import my_functions
import pandas as pd
import pytest


def test_avg_3wk_spend_returns_rolling_mean() -> None:
    spend = pd.Series([10.0, 20.0, 30.0, 40.0])

    result = my_functions.avg_3wk_spend(spend)

    # The first two entries are NaN (window not full), then rolling mean of 3.
    expected = pd.Series([float("nan"), float("nan"), 20.0, 30.0])
    pd.testing.assert_series_equal(result, expected)


def test_spend_per_signup_divides_elementwise() -> None:
    spend = pd.Series([100.0, 200.0])
    signups = pd.Series([10.0, 50.0])

    result = my_functions.spend_per_signup(spend=spend, signups=signups)

    pd.testing.assert_series_equal(result, pd.Series([10.0, 4.0]))


def test_spend_zero_mean_centres_the_series() -> None:
    spend = pd.Series([10.0, 20.0, 30.0])
    spend_mean = 20.0

    result = my_functions.spend_zero_mean(spend=spend, spend_mean=spend_mean)

    pd.testing.assert_series_equal(result, pd.Series([-10.0, 0.0, 10.0]))


@pytest.mark.parametrize(
    ("raw", "expected_first"),
    [
        (pd.Series([0, 1, 2]), 1),  # header sentinel dropped
        (pd.Series([99, 5, 5, 5]), 5),
    ],
)
def test_signups_drops_header_row(raw: pd.Series, expected_first: int) -> None:
    """`pytest.mark.parametrize` is a clean way to cover edge cases."""
    result = my_functions.signups(raw_signups=raw)

    assert result.iloc[0] == expected_first
    assert len(result) == len(raw) - 1
