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

import pandas as pd
import pytest
import ray

from hamilton import base, driver
from hamilton.plugins import h_ray

from .resources import example_module, smoke_screen_module

"""
For reference https://docs.ray.io/en/latest/auto_examples/testing-tips.html
"""


@pytest.fixture(scope="module")
def init():
    ray.init()
    yield "initialized"
    ray.shutdown()


def test_ray_graph_adapter(init):
    initial_columns = {
        "signups": pd.Series([1, 10, 50, 100, 200, 400]),
        "spend": pd.Series([10, 10, 20, 40, 40, 50]),
    }
    dr = driver.Driver(
        initial_columns,
        example_module,
        adapter=h_ray.RayGraphAdapter(base.PandasDataFrameResult()),
    )
    output_columns = [
        "spend",
        "signups",
        "avg_3wk_spend",
        "spend_per_signup",
    ]
    df = dr.execute(output_columns)
    assert set(df) == set(output_columns)
    expected_column = pd.Series(
        [0.0, 0.0, 13.33333, 23.33333, 33.33333, 43.33333], name="avg_3wk_spend"
    )
    pd.testing.assert_series_equal(
        df.avg_3wk_spend.fillna(0.0), expected_column
    )  # fill na to get around NaN
    # TODO: do some more asserting?


def test_smoke_screen_module(init):
    config = {"region": "US"}
    dr = driver.Driver(
        config,
        smoke_screen_module,
        adapter=h_ray.RayGraphAdapter(base.PandasDataFrameResult()),
    )
    output_columns = [
        "raw_acquisition_cost",
        "pessimistic_net_acquisition_cost",
        "neutral_net_acquisition_cost",
        "optimistic_net_acquisition_cost",
        "series_with_start_date_end_date",
    ]
    df = dr.execute(
        inputs={"date_range": {"start_date": "20200101", "end_date": "20220801"}},
        final_vars=output_columns,
    )
    epsilon = 0.00001
    assert abs(df["raw_acquisition_cost"].mean() - 0.393808) < epsilon
    assert abs(df["pessimistic_net_acquisition_cost"].mean() - 0.420769) < epsilon
    assert abs(df["neutral_net_acquisition_cost"].mean() - 0.405582) < epsilon
    assert abs(df["optimistic_net_acquisition_cost"].mean() - 0.399363) < epsilon
    assert df["series_with_start_date_end_date"].iloc[0] == "date_20200101_date_20220801"
