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

from typing import Any, Dict

import polars as pl

if not hasattr(pl, "Series"):
    raise ImportError("Polars is not installed")
from hamilton_sdk.tracking import data_observation
from hamilton_sdk.tracking import polars_col_stats as pls

from hamilton import driver

"""Module that houses functions to compute statistics on polars series/dataframes.
Notes:
 - we should assume a minimum polars version
 - for object types we should :shrug:
 - TBD how close the schemas

"""


dr = driver.Builder().with_modules(pls).with_config({"config_key": "config_value"}).build()


def _compute_stats(df: pl.DataFrame) -> Dict[str, Dict[str, Any]]:
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
    category_types = df.select([pl.col(pl.Categorical)])
    string_types = df.select([pl.col(pl.Utf8)])
    numeric_types = df.select([pl.col(pl.NUMERIC_DTYPES)])
    bool_types = df.select([pl.col(pl.Boolean)])
    # df.select([pl.col(pl.Object)])
    date_types = df.select([pl.col(pl.TEMPORAL_DTYPES)])
    # get all other columns that have not been selected
    # df.select(
    #     ~cs.by_dtype([pl.Categorical, pl.Utf8, pl.Boolean, pl.Object])
    # )  # , pl.TEMPORAL_DTYPES, pl.NUMERIC_DTYPES]))
    column_order = {col: index for index, col in enumerate(df.columns)}
    stats = {}

    def execute_col(target_output: str, col: pl.Series, name: str, position: int) -> Dict[str, Any]:
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
                "base_data_type": "unknown-polars",
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
    for col in date_types.columns:
        stats[col] = execute_col("datetime_column_stats", date_types[col], col, column_order[col])
    for col, position in column_order.items():
        if col not in stats:
            stats[col] = execute_col("unhandled_column_stats", df[col], col, column_order[col])
    return stats


@data_observation.compute_stats.register
def compute_stats_df(result: pl.DataFrame, node_name: str, node_tags: dict) -> Dict[str, Any]:
    return {
        "observability_type": "dagworks_describe",
        "observability_value": _compute_stats(result),
        "observability_schema_version": "0.0.3",
    }


@data_observation.compute_stats.register
def compute_stats_series(result: pl.Series, node_name: str, node_tags: dict) -> Dict[str, Any]:
    return {
        "observability_type": "dagworks_describe",
        "observability_value": _compute_stats(pl.DataFrame({node_name: result})),
        "observability_schema_version": "0.0.3",
    }


if __name__ == "__main__":
    from datetime import date

    df = pl.DataFrame(
        {
            "a": [1, 2, 3, 4, 5],
            # "b": ["a", "b", "c", "d", "e"],
            # "c": [True, False, True, False, True],
            # "d": [1.0, 2.0, 3.0, 4.0, 5.0],
            # "e": pl.Series(["a", "b", "c", "d", "e"], dtype=pl.Categorical),
            # "f": pl.Series(["a", "b", "c", "d", "e"]),
            # "g": pl.Series(["a", "b", "c", "d", "e"]),
            "h": pl.date_range(date(2022, 1, 1), date(2022, 5, 1), "1mo", eager=True),
            # "i": p.Series(["a", "b", "c", "d", "e"], dtype="timedelta64[ns]"),
            "j": pl.Series(
                values=[None, None, None, None, None], name="a", dtype=pl.datatypes.classes.Float64
            ),
        }
    )
    import pprint

    pprint.pprint(compute_stats_df(df, "df"))
