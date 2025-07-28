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
import pyspark.sql as ps

from hamilton.function_modifiers import config
from hamilton.htypes import column as _
from hamilton.plugins import h_spark

IntSeries = _[pd.Series, int]
FloatSeries = _[pd.Series, float]


def a(a_raw: IntSeries) -> IntSeries:
    return a_raw + 1


def b(b_raw: IntSeries) -> IntSeries:
    return b_raw + 3


def c(c_raw: IntSeries) -> FloatSeries:
    return c_raw * 3.5


def a_times_key(a: IntSeries, key: IntSeries) -> IntSeries:
    return a * key


def b_times_key(b: IntSeries, key: IntSeries) -> IntSeries:
    return b * key


def a_plus_b_plus_c(a: IntSeries, b: IntSeries, c: FloatSeries) -> FloatSeries:
    return a + b + c


def df_1(spark_session: ps.SparkSession) -> ps.DataFrame:
    df = pd.DataFrame.from_records(
        [
            {"key": 1, "a_raw": 1, "b_raw": 2, "c_raw": 1},
            {"key": 2, "a_raw": 4, "b_raw": 5, "c_raw": 2},
            {"key": 3, "a_raw": 7, "b_raw": 8, "c_raw": 3},
            {"key": 4, "a_raw": 10, "b_raw": 11, "c_raw": 4},
            {"key": 5, "a_raw": 13, "b_raw": 14, "c_raw": 5},
        ]
    )
    return spark_session.createDataFrame(df)


@h_spark.with_columns(
    a,
    b,
    c,
    a_times_key,
    b_times_key,
    a_plus_b_plus_c,
    select=["a_times_key", "b_times_key", "a_plus_b_plus_c"],
    columns_to_pass=["a_raw", "b_raw", "c_raw", "key"],
)
@config.when_not_in(mode=["select", "select_decorator"])
def processed_df_as_pandas__append(df_1: ps.DataFrame) -> pd.DataFrame:
    return df_1.select("a_times_key", "b_times_key", "a_plus_b_plus_c").toPandas()


@h_spark.with_columns(
    a,
    b,
    c,
    a_times_key,
    b_times_key,
    a_plus_b_plus_c,
    select=["a_times_key", "a_plus_b_plus_c"],
    columns_to_pass=["a_raw", "b_raw", "c_raw", "key"],
    mode="select",
)
@config.when(mode="select")
def processed_df_as_pandas__select(df_1: ps.DataFrame) -> pd.DataFrame:
    # This should have two columns
    return df_1.toPandas()


@h_spark.select(
    a,
    b,
    c,
    a_times_key,
    b_times_key,
    a_plus_b_plus_c,
    columns_to_pass=["a_raw", "b_raw", "c_raw", "key"],
    output_cols=["a_times_key", "a_plus_b_plus_c"],
)
@config.when(mode="select_decorator")
def processed_df_as_pandas__select_decorator(df_1: ps.DataFrame) -> pd.DataFrame:
    # This should have two columns
    return df_1.toPandas()
