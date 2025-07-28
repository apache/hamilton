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

import polars as pl
from polars.testing import assert_frame_equal

from hamilton import driver

from .resources import with_columns_end_to_end_lazy


def test_end_to_end_with_columns_automatic_extract_lazy():
    config_5 = {
        "factor": 5,
    }
    dr = driver.Builder().with_modules(with_columns_end_to_end_lazy).with_config(config_5).build()
    result = dr.execute(final_vars=["final_df"], inputs={"user_factor": 1000})["final_df"]

    expected_df = pl.DataFrame(
        {
            "col_1": [1, 2, 3, 4],
            "col_2": [11, 12, 13, 14],
            "col_3": [1, 1, 1, 1],
            "subtract_1_from_2": [10, 10, 10, 10],
            "multiply_3": [5, 5, 5, 5],
            "add_1_by_user_adjustment_factor": [1001, 1002, 1003, 1004],
            "multiply_2_by_upstream_3": [33, 36, 39, 42],
        }
    )
    pl.testing.assert_frame_equal(result.collect(), expected_df)

    config_7 = {
        "factor": 7,
    }
    dr = driver.Builder().with_modules(with_columns_end_to_end_lazy).with_config(config_7).build()
    result = dr.execute(final_vars=["final_df"], inputs={"user_factor": 1000})["final_df"]

    expected_df = pl.DataFrame(
        {
            "col_1": [1, 2, 3, 4],
            "col_2": [11, 12, 13, 14],
            "col_3": [1, 1, 1, 1],
            "subtract_1_from_2": [10, 10, 10, 10],
            "multiply_3": [7, 7, 7, 7],
            "add_1_by_user_adjustment_factor": [1001, 1002, 1003, 1004],
            "multiply_2_by_upstream_3": [33, 36, 39, 42],
        }
    )
    assert_frame_equal(result.collect(), expected_df)


def test_end_to_end_with_columns_pass_dataframe_lazy():
    config_5 = {
        "factor": 5,
    }
    dr = driver.Builder().with_modules(with_columns_end_to_end_lazy).with_config(config_5).build()

    result = dr.execute(final_vars=["final_df_2"])["final_df_2"]
    expected_df = pl.DataFrame(
        {
            "col_1": [1, 2, 3, 4],
            "col_2": [11, 12, 13, 14],
            "col_3": [1, 1, 1, 1],
            "multiply_1": [5, 10, 15, 20],
        }
    )
    assert_frame_equal(result.collect(), expected_df)
