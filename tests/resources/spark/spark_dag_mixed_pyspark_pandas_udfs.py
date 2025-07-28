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

from typing import Callable, List

import pandas as pd
import pyspark.sql as ps

from hamilton.function_modifiers import parameterize, value
from hamilton.htypes import column as _
from hamilton.plugins import h_spark

IntSeries = _[pd.Series, int]
FloatSeries = _[pd.Series, float]


def to_add() -> int:
    return 1


def spark_session() -> ps.SparkSession:
    spark = (
        ps.SparkSession.builder.master("local")
        .appName("spark session")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )
    return spark


def _module(user_controls_initial_dataframe: bool) -> List[Callable]:
    out = []
    if user_controls_initial_dataframe:

        @parameterize(
            a_raw={"col": value("a_raw")},
            b_raw={"col": value("b_raw")},
            c_raw={"col": value("c_raw")},
            key={"col": value("key")},
        )
        def raw_col(external_dataframe: ps.DataFrame, col: str) -> ps.Column:
            return external_dataframe[col]

        out.append(raw_col)

    def a(a_raw: ps.DataFrame, to_add: int) -> ps.DataFrame:
        return a_raw.withColumn("a", a_raw.a_raw + to_add)

    def b(b_raw: ps.DataFrame, b_add: int = 3) -> ps.Column:
        return b_raw["b_raw"] + b_add

    def c(c_raw: IntSeries) -> FloatSeries:
        return c_raw * 3.5

    @h_spark.require_columns("a", "key")
    def a_times_key(a_key: ps.DataFrame, identity_multiplier: int = 1) -> ps.Column:
        return a_key.a * a_key.key * identity_multiplier

    def b_times_key(b: IntSeries, key: IntSeries) -> IntSeries:
        return b * key

    @h_spark.require_columns("a", "b", "c")
    def a_plus_b_plus_c(a_b_c: ps.DataFrame) -> ps.Column:
        return a_b_c.a + a_b_c.b + a_b_c.c

    out.extend([a, b, c, a_times_key, b_times_key, a_plus_b_plus_c])
    return out


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
    *_module(False),
    select=["a_times_key", "b_times_key", "a_plus_b_plus_c"],
    columns_to_pass=["a_raw", "b_raw", "c_raw", "key"],
)
def processed_df_as_pandas(df_1: ps.DataFrame) -> pd.DataFrame:
    return df_1.select("a_times_key", "b_times_key", "a_plus_b_plus_c").toPandas()


@h_spark.with_columns(
    *_module(True),
    select=["a_times_key", "b_times_key", "a_plus_b_plus_c"],
    pass_dataframe_as="external_dataframe",
)
def processed_df_as_pandas_dataframe_with_injected_dataframe(df_1: ps.DataFrame) -> pd.DataFrame:
    return df_1.select("a_times_key", "b_times_key", "a_plus_b_plus_c").toPandas()
