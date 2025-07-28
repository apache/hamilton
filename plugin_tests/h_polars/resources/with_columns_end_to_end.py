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

from hamilton.function_modifiers import config
from hamilton.plugins.h_polars import with_columns


def upstream_factor() -> int:
    return 3


def initial_df() -> pl.DataFrame:
    return pl.DataFrame({"col_1": [1, 2, 3, 4], "col_2": [11, 12, 13, 14], "col_3": [1, 1, 1, 1]})


def subtract_1_from_2(col_1: pl.Series, col_2: pl.Series) -> pl.Series:
    return col_2 - col_1


@config.when(factor=5)
def multiply_3__by_5(col_3: pl.Series) -> pl.Series:
    return col_3 * 5


@config.when(factor=7)
def multiply_3__by_7(col_3: pl.Series) -> pl.Series:
    return col_3 * 7


def add_1_by_user_adjustment_factor(col_1: pl.Series, user_factor: int) -> pl.Series:
    return col_1 + user_factor


def multiply_2_by_upstream_3(col_2: pl.Series, upstream_factor: int) -> pl.Series:
    return col_2 * upstream_factor


@with_columns(
    subtract_1_from_2,
    multiply_3__by_5,
    multiply_3__by_7,
    add_1_by_user_adjustment_factor,
    multiply_2_by_upstream_3,
    columns_to_pass=["col_1", "col_2", "col_3"],
    select=[
        "subtract_1_from_2",
        "multiply_3",
        "add_1_by_user_adjustment_factor",
        "multiply_2_by_upstream_3",
    ],
    namespace="some_subdag",
)
def final_df(initial_df: pl.DataFrame) -> pl.DataFrame:
    return initial_df


def col_3(initial_df: pl.DataFrame) -> pl.Series:
    return pl.Series([0, 2, 4, 6])


@with_columns(
    col_3,
    multiply_3__by_5,
    multiply_3__by_7,
    on_input="initial_df",
    select=["col_3", "multiply_3"],
)
def final_df_2(initial_df: pl.DataFrame) -> pl.DataFrame:
    return initial_df
