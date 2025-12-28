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

from typing import Any, List

import pandas as pd

from hamilton.function_modifiers import hamilton_exclude, pipe_output, source, step, value


# data1 and data2
@hamilton_exclude
def filter_(some_data: pd.DataFrame) -> pd.DataFrame:
    return some_data.dropna()


@hamilton_exclude
def test_foo(a, b, c):
    return a + b + c


# data 2
# this is for value
@hamilton_exclude
def add_missing_value(some_data: pd.DataFrame, missing_row: List[Any]) -> pd.DataFrame:
    some_data.loc[-1] = missing_row
    return some_data


# data 2
# this is for source
@hamilton_exclude
def join(some_data: pd.DataFrame, other_data: pd.DataFrame) -> pd.DataFrame:
    return some_data.set_index("col_2").join(other_data.set_index("col_1"))


# data1 and data2
@hamilton_exclude
def sort(some_data: pd.DataFrame) -> pd.DataFrame:
    columns = some_data.columns
    return some_data.sort_values(by=columns[0])


@pipe_output(
    step(filter_),
    step(sort),
)
def data_1() -> pd.DataFrame:
    df = pd.DataFrame.from_dict({"col_1": [3, 2, pd.NA, 0], "col_2": ["a", "b", pd.NA, "d"]})
    return df


@pipe_output(
    step(filter_),
    step(add_missing_value, missing_row=value(["c", 145])),
    step(join, other_data=source("data_3")),
    step(sort),
)
def data_2() -> pd.DataFrame:
    df = pd.DataFrame.from_dict(
        {"col_1": ["a", "b", pd.NA, "d", "e"], "col_2": [150, 155, 145, 200, 5000]}
    )
    return df


def data_3() -> pd.DataFrame:
    df = pd.DataFrame.from_dict({"col_1": [150, 155, 145, 200, 5000], "col_2": [10, 23, 32, 50, 0]})
    return df


def feat_A(data_1: pd.DataFrame, data_2: pd.DataFrame) -> pd.DataFrame:
    return (
        data_1.set_index("col_2").join(data_2.reset_index(names=["col_3"]).set_index("col_1"))
    ).reset_index(names=["col_0"])
