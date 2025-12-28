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

from hamilton.function_modifiers import mutate, source, value


def data_1() -> pd.DataFrame:
    df = pd.DataFrame.from_dict({"col_1": [3, 2, pd.NA, 0], "col_2": ["a", "b", pd.NA, "d"]})
    return df


def data_2() -> pd.DataFrame:
    df = pd.DataFrame.from_dict(
        {"col_1": ["a", "b", pd.NA, "d", "e"], "col_2": [150, 155, 145, 200, 5000]}
    )
    return df


def data_3() -> pd.DataFrame:
    df = pd.DataFrame.from_dict({"col_1": [150, 155, 145, 200, 5000], "col_2": [10, 23, 32, 50, 0]})
    return df


# data1 and data2
@mutate(data_1, data_2)
def filter_(some_data: pd.DataFrame) -> pd.DataFrame:
    """Remove NAN values.

    Decorated with mutate this will be applied to both data_1 and data_2.
    """
    return some_data.dropna()


# data 2
# this is for value
@mutate(data_2, missing_row=value(["c", 145]))
def add_missing_value(some_data: pd.DataFrame, missing_row: List[Any]) -> pd.DataFrame:
    """Add row to dataframe.

    The functions decorated with mutate can be viewed as steps in pipe_output in the order they
    are implemented. This means that data_2 had a row removed with NAN and here we add back a row
    by hand that replaces that row.
    """
    some_data.loc[-1] = missing_row
    return some_data


# data 2
# this is for source
@mutate(data_2, other_data=source("data_3"))
def join(some_data: pd.DataFrame, other_data: pd.DataFrame) -> pd.DataFrame:
    """Join two dataframes.

    We can use results from other nodes in the DAG by using the `source` functionality. Here we join
    data_2 table with another table - data_3 - that is the output of another node.
    """
    return some_data.set_index("col_2").join(other_data.set_index("col_1"))


# data1 and data2
@mutate(data_1, data_2)
def sort(some_data: pd.DataFrame) -> pd.DataFrame:
    """Sort dataframes by first column.

    This is the last step of our pipeline(s) and gets again applied to data_1 and data_2. We did some
    light pre-processing on data_1 by removing NANs and sorting and more elaborate pre-processing on
    data_2 where we added values and joined another table.
    """
    columns = some_data.columns
    return some_data.sort_values(by=columns[0])


def feat_A(data_1: pd.DataFrame, data_2: pd.DataFrame) -> pd.DataFrame:
    """Combining two raw dataframes to create a feature."""
    return (
        data_1.set_index("col_2").join(data_2.reset_index(names=["col_3"]).set_index("col_1"))
    ).reset_index(names=["col_0"])
