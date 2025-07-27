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

import functools
from typing import Any, Dict, List, Optional

import pyspark.sql as ps
from hamilton_sdk.tracking import data_observation
from hamilton_sdk.tracking.data_observation import ObservationType

try:
    from hamilton.plugins import h_schema
except (ImportError, ModuleNotFoundError):
    h_schema = None

"""Module that houses functions to introspect a PySpark dataframe.
"""
# this is a mapping used in the Backend/UI.
# we should probably move this to a shared location.
base_data_type_mapping = {
    "timestamp": "datetime",
    "date": "datetime",
    "string": "str",
    "integer": "numeric",
    "double": "numeric",
    "float": "numeric",
    "boolean": "boolean",
    "long": "numeric",
    "short": "numeric",
}

base_schema = {
    # we can't get all of these about a pyspark dataframe
    "base_data_type": None,
    # 'count': 0,
    "data_type": None,
    # 'histogram': {},
    # 'max': 0,
    # 'mean': 0,
    # 'min': 0,
    # 'missing': 0,
    "name": None,
    "pos": None,
    # 'quantiles': {},
    # 'std': 0,
    # 'zeros': 0
}


# quick cache to ensure we don't compute twice
@functools.lru_cache(maxsize=128)
def _introspect(df: ps.DataFrame) -> Dict[str, Any]:
    """Introspect a PySpark dataframe and return a dictionary of statistics.

    :param df: PySpark dataframe to introspect.
    :return: Dictionary of column to metadata about it.
    """
    fields = df.schema.jsonValue()["fields"]
    column_to_metadata = []
    for idx, field in enumerate(fields):
        values = base_schema.copy()
        values.update(
            {
                "name": field["name"],
                "pos": idx,
                "data_type": field["type"],
                "base_data_type": base_data_type_mapping.get(field["type"], "unhandled"),
                "nullable": field["nullable"],
            }
        )
        column_to_metadata.append(values)
    cost_explain = df._sc._jvm.PythonSQLUtils.explainString(df._jdf.queryExecution(), "cost")
    extended_explain = df._sc._jvm.PythonSQLUtils.explainString(
        df._jdf.queryExecution(), "extended"
    )
    return {
        "columns": column_to_metadata,
        "cost_explain": cost_explain,
        "extended_explain": extended_explain,
    }


@data_observation.compute_stats.register
def compute_stats_psdf(result: ps.DataFrame, node_name: str, node_tags: dict) -> ObservationType:
    # TODO: create custom type instead of dict for UI
    o_value = _introspect(result)

    return {
        "observability_type": "dict",
        "observability_value": {
            "type": str(type(result)),
            "value": o_value,
        },
        "observability_schema_version": "0.0.2",
    }


@data_observation.compute_schema.register
def compute_schema_psdf(
    result: ps.DataFrame, node_name: str, node_tags: dict
) -> Optional[ObservationType]:
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


@data_observation.compute_additional_results.register
def compute_additional_psdf(
    result: ps.DataFrame, node_name: str, node_tags: dict
) -> List[ObservationType]:
    o_value = _introspect(result)
    return [
        {
            "observability_type": "primitive",
            "observability_value": {
                "type": str(str),
                "value": o_value["cost_explain"],
            },
            "observability_schema_version": "0.0.1",
            "name": "Cost Explain",
        },
        {
            "observability_type": "primitive",
            "observability_value": {
                "type": str(str),
                "value": o_value["extended_explain"],
            },
            "observability_schema_version": "0.0.1",
            "name": "Extended Explain",
        },
    ]


if __name__ == "__main__":
    import numpy as np
    import pandas as pd

    df = pd.DataFrame(
        {
            "a": [1, 2, 3, 4, 5],
            "b": ["a", "b", "c", "d", "e"],
            "c": [True, False, True, False, True],
            "d": [1.0, 2.0, 3.0, 4.0, 5.0],
            "e": pd.Categorical(["a", "b", "c", "d", "e"]),
            "f": pd.Series(["a", "b", "c", "d", "e"], dtype="string"),
            "g": pd.Series(["a", "b", "c", "d", "e"], dtype="object"),
            "h": pd.Series(
                ["20221231", None, "20221231", "20221231", "20221231"], dtype="datetime64[ns]"
            ),
            "i": pd.Series([None, None, None, None, None], name="a", dtype=np.float64),
            "j": pd.Series(name="a", data=pd.date_range("20230101", "20230105")),
        }
    )
    spark = ps.SparkSession.builder.master("local[1]").getOrCreate()
    psdf = spark.createDataFrame(df)
    import pprint

    res = compute_stats_psdf(psdf, "df", {})
    pprint.pprint(res)
