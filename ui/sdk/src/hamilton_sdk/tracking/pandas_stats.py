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

from typing import Any, Dict, Optional, Union

import pandas as pd
from hamilton_sdk.tracking import data_observation
from hamilton_sdk.tracking import pandas_col_stats as pcs

from hamilton import driver

try:
    from hamilton.plugins import h_schema
except (ImportError, ModuleNotFoundError):
    h_schema = None

"""Module that houses functions to compute statistics on pandas series/dataframes.
Notes:
 - we should assume pandas v1.0+ so that we have a string type
 - for object types we should :shrug:
"""

dr = driver.Builder().with_modules(pcs).with_config({"config_key": "config_value"}).build()


def _compute_stats(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Compute statistics on a pandas dataframe.
    for each c in [dataframe|series]:
        if c is numeric:
            compute numeric stats
        elif c is string:
            compute string stats
        elif c is datetime:
            compute datetime stats
        elif c is object:
            # try to figure out object
        elif c is geometry:
            # try to figure out geometry
    """
    category_types = df.select_dtypes(include=["category"])
    string_types = df.select_dtypes(include=["string"])
    numeric_types = df.select_dtypes(include=["number"])
    bool_types = df.select_dtypes(include=["bool"])
    object_types = df.select_dtypes(include=["object"])
    datetime_types = df.select_dtypes(include=["datetime", "timedelta"])
    unhandled_types = df.select_dtypes(
        exclude=["string", "category", "number", "bool", "object", "datetime", "timedelta"]
    )
    column_order = {col: index for index, col in enumerate(df.columns)}
    stats = {}

    def execute_col(
        target_output: str, col: pd.Series, name: Union[str, int], position: int
    ) -> Dict[str, Any]:
        """Get stats on a column."""
        try:
            res = dr.execute(
                [target_output], inputs={"col": col, "name": name, "position": position}
            )
            res = res[target_output].to_dict()
        except Exception:
            # minimum that we want -- ideally we have hamilton handle errors and do best effort.
            res = {
                "name": name,
                "pos": position,
                "data_type": str(col.dtype),
                "base_data_type": "unknown-pandas",
            }
        return res

    for col in category_types.columns:
        stats[col] = execute_col(
            "category_column_stats", category_types[col], col, column_order[col]
        )
    for col in string_types.columns:
        stats[col] = execute_col("string_column_stats", string_types[col], col, column_order[col])
    for col in numeric_types.columns:
        stats[col] = execute_col("numeric_column_stats", numeric_types[col], col, column_order[col])
    for col in bool_types.columns:
        stats[col] = execute_col("boolean_column_stats", bool_types[col], col, column_order[col])
    for col in datetime_types.columns:
        stats[col] = execute_col(
            "datetime_column_stats", datetime_types[col], col, column_order[col]
        )
    for col in list(object_types.columns) + list(unhandled_types.columns):
        stats[col] = execute_col("unhandled_column_stats", df[col], col, column_order[col])
    return stats


@data_observation.compute_stats.register
def compute_stats_df(
    result: pd.DataFrame, node_name: str, node_tags: dict
) -> data_observation.ObservationType:
    summary_stats = _compute_stats(result)

    return {
        "observability_type": "dagworks_describe",
        "observability_value": summary_stats,
        "observability_schema_version": "0.0.3",
    }


@data_observation.compute_schema.register
def compute_schema(
    result: pd.DataFrame, node_name: str, node_tags: dict
) -> Optional[data_observation.ObservationType]:
    if h_schema is not None:
        schema = h_schema._get_arrow_schema(result)
        schema.with_metadata(dict(name=node_name))
        return {
            "observability_type": "schema",
            "observability_value": h_schema.pyarrow_schema_to_json(schema),
            "observability_schema_version": "0.0.1",
            "name": "Schema",
        }
    return None


@data_observation.compute_stats.register
def compute_stats_series(result: pd.Series, node_name: str, node_tags: dict) -> Dict[str, Any]:
    col_name = result.name if result.name else node_name
    return {
        "observability_type": "dagworks_describe",
        "observability_value": _compute_stats(pd.DataFrame({col_name: result})),
        "observability_schema_version": "0.0.3",
    }


if __name__ == "__main__":
    df = pd.DataFrame(
        {
            # "a": [1, 2, 3, 4, 5],
            # "b": ["a", "b", "c", "d", "e"],
            # "c": [True, False, True, False, True],
            # "d": [1.0, 2.0, 3.0, 4.0, 5.0],
            # "e": pd.Categorical(["a", "b", "c", "d", "e"]),
            # "f": pd.Series(["a", "b", "c", "d", "e"], dtype="string"),
            # "g": pd.Series(["a", "b", "c", "d", "e"], dtype="object"),
            # "h": pd.Series(
            #     ["20221231", None, "20221231", "20221231", "20221231"], dtype="datetime64[ns]"
            # ),
            # "i": pd.Series([None, None, None, None, None], name="a", dtype=np.float64),
            "j": pd.Series(name="a", data=pd.date_range("20230101", "20230105")),
        }
    )
    import pprint

    res = compute_stats_df(df, "df")
    pprint.pprint(res)
    # create a pandas series of type datetime
    s = pd.Series(["20221231"], dtype="datetime64[ns]")
    import json

    json.dumps(res)
