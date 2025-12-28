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

from typing import Any, Dict, List

import pandas as pd

from hamilton.function_modifiers import (
    apply_to,
    extract_columns,
    extract_fields,
    mutate,
    source,
    value,
)


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


@extract_fields({"field_1": pd.Series, "field_2": pd.Series})
def feat_A(data_1: pd.DataFrame, data_2: pd.DataFrame) -> Dict[str, pd.Series]:
    df = (
        data_1.set_index("col_2").join(data_2.reset_index(names=["col_3"]).set_index("col_1"))
    ).reset_index(names=["col_0"])
    return {"field_1": df.iloc[:, 1], "field_2": df.iloc[:, 2]}


@extract_columns("col_2", "col_3")
def feat_B(data_1: pd.DataFrame, data_2: pd.DataFrame) -> pd.DataFrame:
    return (
        data_1.set_index("col_2").join(data_2.reset_index(names=["col_3"]).set_index("col_1"))
    ).reset_index(names=["col_0"])


def feat_C(field_1: pd.Series, col_3: pd.Series) -> pd.DataFrame:
    return pd.concat([field_1, col_3], axis=1)


def feat_D(field_2: pd.Series, col_2: pd.Series) -> pd.DataFrame:
    return pd.concat([field_2, col_2], axis=1)


# data1 and data2
@mutate(apply_to(data_1).when_in(a=[1, 2, 3]), apply_to(data_2).when_not_in(a=[1, 2, 3]))
def filter_(some_data: pd.DataFrame) -> pd.DataFrame:
    """Remove NAN values.

    Mutate accepts a `config.*` family conditional where we can choose when the transform will be applied
    onto the target function.
    """
    return some_data.dropna()


# data 2
# this is for value
@mutate(apply_to(data_2), missing_row=value(["c", 145]))
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
@mutate(
    apply_to(data_2).named(name="", namespace="some_random_namespace"), other_data=source("data_3")
)
def join(some_data: pd.DataFrame, other_data: pd.DataFrame) -> pd.DataFrame:
    """Join two dataframes.

    We can use results from other nodes in the DAG by using the `source` functionality. Here we join
    data_2 table with another table - data_3 - that is the output of another node.

    In addition, mutate also support adding custom names to the nodes.
    """
    return some_data.set_index("col_2").join(other_data.set_index("col_1"))


# data1 and data2
@mutate(apply_to(data_1), apply_to(data_2))
def sort(some_data: pd.DataFrame) -> pd.DataFrame:
    """Sort dataframes by first column.

    This is the last step of our pipeline(s) and gets again applied to data_1 and data_2. We did some
    light pre-processing on data_1 by removing NANs and sorting and more elaborate pre-processing on
    data_2 where we added values and joined another table.
    """
    columns = some_data.columns
    return some_data.sort_values(by=columns[0])


# we want to apply some adjustment coefficient to all the columns of feat_B, but only to field_1 of feat_A
@mutate(
    apply_to(feat_A, factor=value(100)).on_output("field_1").named("Europe"),
    apply_to(feat_B, factor=value(10)).named("US"),
)
def _adjustment_factor(some_data: pd.Series, factor: float) -> pd.Series:
    """Adjust the value by some factor.

    You can imagine this step occurring later in time. We first constructed our DAG with features A and
    B only to realize that something is off. We are now experimenting post-hoc to improve and find the
    best possible features.

    We first split the features by columns of interest and then adjust them by a regional factor to
    combine them into improved features we can use further down the pipeline.
    """
    return some_data * factor
