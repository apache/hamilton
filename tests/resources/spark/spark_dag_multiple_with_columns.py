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


def const_1() -> float:
    return 4.3


# Placing these functions here so we don't try to read the DAG
# This tests the mixing of different types, which is *only* allowed
# inside the with_columns subdag, and not yet allowed within Hamilton
# as hamilton doesn't know that they will compile to the same nodes


def _df_2_modules():
    def d(d_raw: IntSeries) -> IntSeries:
        return d_raw + 5

    def e(e_raw: int, d: int, const_1: float) -> float:
        return e_raw + d + const_1

    def f(f_raw: int) -> float:
        return f_raw * 3.5

    def multiply_d_e_f_key(
        d: IntSeries, e: FloatSeries, f: FloatSeries, key: IntSeries
    ) -> FloatSeries:
        return d * e * f * key

    return [d, e, f, multiply_d_e_f_key]


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
    # TODO -- have a pool (module, rather than function) that we can select *from*
    # Or just select in the processed_df?
    a,
    b,
    c,
    a_times_key,
    b_times_key,
    a_plus_b_plus_c,
    select=["a_times_key", "b_times_key", "a_plus_b_plus_c"],
    columns_to_pass=["a_raw", "b_raw", "c_raw", "key"],
)
def processed_df_1(df_1: ps.DataFrame) -> ps.DataFrame:
    return df_1.select("key", "a_times_key", "b_times_key", "a_plus_b_plus_c")


def df_2(spark_session: ps.SparkSession) -> ps.DataFrame:
    df = pd.DataFrame.from_records(
        [
            {"key": 1, "d_raw": 1, "e_raw": 2, "f_raw": 5},
            {"key": 2, "d_raw": 4, "e_raw": 5, "f_raw": 10},
            {"key": 3, "d_raw": 7, "e_raw": 8, "f_raw": 15},
            {"key": 4, "d_raw": 10, "e_raw": 11, "f_raw": 20},
        ]
    )
    return spark_session.createDataFrame(df)


@h_spark.with_columns(
    *_df_2_modules(),
    select=["multiply_d_e_f_key", "d", "e", "f"],
    columns_to_pass=["d_raw", "e_raw", "f_raw", "key"],
)
def processed_df_2_joined_df_1(df_2: ps.DataFrame, processed_df_1: ps.DataFrame) -> ps.DataFrame:
    return df_2.join(processed_df_1, processed_df_1["key"] == df_2["key"], "inner").drop(df_2.key)


def final(processed_df_2_joined_df_1: ps.DataFrame) -> pd.DataFrame:
    return processed_df_2_joined_df_1.toPandas()
