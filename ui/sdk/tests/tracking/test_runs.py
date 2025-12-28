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

import json
from datetime import date
from typing import Any

import numpy as np
import pandas as pd
import polars as pl
import pytest
from hamilton_sdk.tracking import runs

from hamilton import node

result_base = {
    "observability_type": "REPLACE_ME",
    "observability_value": None,
    "observability_schema_version": "0.0.3",
}


def default_func() -> Any:
    return None


def create_node(name: str, type_: type) -> node.Node:
    return node.Node(name, type_, "", default_func)


@pytest.mark.parametrize(
    "test_result,test_node,observability_type,stats",
    [
        (
            pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}),
            create_node("test", pd.DataFrame),
            "dagworks_describe",
            {
                "a": {
                    "count": 3,
                    "data_type": "int64",
                    "histogram": {
                        "(0.997, 1.2]": 1,
                        "(1.2, 1.4]": 0,
                        "(1.4, 1.6]": 0,
                        "(1.6, 1.8]": 0,
                        "(1.8, 2.0]": 1,
                        "(2.0, 2.2]": 0,
                        "(2.2, 2.4]": 0,
                        "(2.4, 2.6]": 0,
                        "(2.6, 2.8]": 0,
                        "(2.8, 3.0]": 1,
                    },
                    "max": 3,
                    "mean": 2.0,
                    "min": 1,
                    "missing": 0,
                    "name": "a",
                    "pos": 0,
                    "quantiles": {0.1: 1.2, 0.25: 1.5, 0.5: 2.0, 0.75: 2.5, 0.9: 2.8},
                    "std": 1.0,
                    "zeros": 0,
                    "base_data_type": "numeric",
                },
                "b": {
                    "count": 3,
                    "data_type": "int64",
                    "histogram": {
                        "(3.9970000000000003, 4.2]": 1,
                        "(4.2, 4.4]": 0,
                        "(4.4, 4.6]": 0,
                        "(4.6, 4.8]": 0,
                        "(4.8, 5.0]": 1,
                        "(5.0, 5.2]": 0,
                        "(5.2, 5.4]": 0,
                        "(5.4, 5.6]": 0,
                        "(5.6, 5.8]": 0,
                        "(5.8, 6.0]": 1,
                    },
                    "max": 6,
                    "mean": 5.0,
                    "min": 4,
                    "missing": 0,
                    "name": "b",
                    "pos": 1,
                    "quantiles": {0.1: 4.2, 0.25: 4.5, 0.5: 5.0, 0.75: 5.5, 0.9: 5.8},
                    "std": 1.0,
                    "zeros": 0,
                    "base_data_type": "numeric",
                },
            },
        ),
        (
            pd.Series([1, 2, 3], name="a"),
            create_node("a", pd.Series),
            "dagworks_describe",
            {
                "a": {
                    "count": 3,
                    "data_type": "int64",
                    "histogram": {
                        "(0.997, 1.2]": 1,
                        "(1.2, 1.4]": 0,
                        "(1.4, 1.6]": 0,
                        "(1.6, 1.8]": 0,
                        "(1.8, 2.0]": 1,
                        "(2.0, 2.2]": 0,
                        "(2.2, 2.4]": 0,
                        "(2.4, 2.6]": 0,
                        "(2.6, 2.8]": 0,
                        "(2.8, 3.0]": 1,
                    },
                    "max": 3,
                    "mean": 2.0,
                    "min": 1,
                    "missing": 0,
                    "name": "a",
                    "pos": 0,
                    "quantiles": {0.1: 1.2, 0.25: 1.5, 0.5: 2.0, 0.75: 2.5, 0.9: 2.8},
                    "std": 1.0,
                    "zeros": 0,
                    "base_data_type": "numeric",
                }
            },
        ),
        (
            pd.Series([None, None, None, None, None], name="a", dtype=np.float64),
            create_node("a", pd.Series),
            "dagworks_describe",
            {
                "a": {
                    "count": 5,
                    "data_type": "float64",
                    "histogram": {},
                    "max": None,
                    "mean": None,
                    "min": None,
                    "missing": 5,
                    "name": "a",
                    "pos": 0,
                    "quantiles": {0.1: None, 0.25: None, 0.5: None, 0.75: None, 0.9: None},
                    "std": None,
                    "zeros": 0,
                    "base_data_type": "numeric",
                }
            },
        ),
        (
            pd.Series(name="a", data=pd.date_range("20230101", "20230103")),
            create_node("a", pd.Series),
            "dagworks_describe",
            {
                "a": {
                    "base_data_type": "datetime",
                    "count": 3,
                    "data_type": "datetime64[ns]",
                    "histogram": {
                        "(2022-12-31 23:57:07.199999999, 2023-01-01 04:48:00]": 1,
                        "(2023-01-01 04:48:00, 2023-01-01 09:36:00]": 0,
                        "(2023-01-01 09:36:00, 2023-01-01 14:24:00]": 0,
                        "(2023-01-01 14:24:00, 2023-01-01 19:12:00]": 0,
                        "(2023-01-01 19:12:00, 2023-01-02 00:00:00]": 1,
                        "(2023-01-02 00:00:00, 2023-01-02 04:48:00]": 0,
                        "(2023-01-02 04:48:00, 2023-01-02 09:36:00]": 0,
                        "(2023-01-02 09:36:00, 2023-01-02 14:24:00]": 0,
                        "(2023-01-02 14:24:00, 2023-01-02 19:12:00]": 0,
                        "(2023-01-02 19:12:00, 2023-01-03 00:00:00]": 1,
                    },
                    "max": "2023-01-03T00:00:00",
                    "mean": "2023-01-02T00:00:00",
                    "min": "2023-01-01T00:00:00",
                    "missing": 0,
                    "name": "a",
                    "pos": 0,
                    "quantiles": {
                        0.1: "2023-01-01T04:48:00",
                        0.25: "2023-01-01T12:00:00",
                        0.5: "2023-01-02T00:00:00",
                        0.75: "2023-01-02T12:00:00",
                        0.9: "2023-01-02T19:12:00",
                    },
                    "std": "P1DT0H0M0S",
                    "zeros": 0,
                }
            },
        ),
        (
            pd.Series(name="a", data=[pd.NaT] * 3),
            create_node("a", pd.Series),
            "dagworks_describe",
            {
                "a": {
                    "base_data_type": "datetime",
                    "count": 3,
                    "data_type": "datetime64[ns]",
                    "histogram": {},
                    "max": None,
                    "mean": None,
                    "min": None,
                    "missing": 3,
                    "name": "a",
                    "pos": 0,
                    "quantiles": {0.1: None, 0.25: None, 0.5: None, 0.75: None, 0.9: None},
                    "std": None,
                    "zeros": 0,
                }
            },
        ),
        (
            np.array([[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]]),
            create_node("test", np.ndarray),
            "dagworks_describe",
            {
                0: {
                    "base_data_type": "numeric",
                    "count": 4,
                    "data_type": "int64",
                    "histogram": {
                        "(0.9989, 0.9992]": 0,
                        "(0.9992, 0.9994]": 0,
                        "(0.9994, 0.9996]": 0,
                        "(0.9996, 0.9998]": 0,
                        "(0.9998, 1.0]": 4,
                        "(1.0, 1.0002]": 0,
                        "(1.0002, 1.0004]": 0,
                        "(1.0004, 1.0006]": 0,
                        "(1.0006, 1.0008]": 0,
                        "(1.0008, 1.001]": 0,
                    },
                    "max": 1,
                    "mean": 1.0,
                    "min": 1,
                    "missing": 0,
                    "name": 0,
                    "pos": 0,
                    "quantiles": {0.1: 1.0, 0.25: 1.0, 0.5: 1.0, 0.75: 1.0, 0.9: 1.0},
                    "std": 0.0,
                    "zeros": 0,
                },
                1: {
                    "base_data_type": "numeric",
                    "count": 4,
                    "data_type": "int64",
                    "histogram": {
                        "(1.9979, 1.9984]": 0,
                        "(1.9984, 1.9988]": 0,
                        "(1.9988, 1.9992]": 0,
                        "(1.9992, 1.9996]": 0,
                        "(1.9996, 2.0]": 4,
                        "(2.0, 2.0004]": 0,
                        "(2.0004, 2.0008]": 0,
                        "(2.0008, 2.0012]": 0,
                        "(2.0012, 2.0016]": 0,
                        "(2.0016, 2.002]": 0,
                    },
                    "max": 2,
                    "mean": 2.0,
                    "min": 2,
                    "missing": 0,
                    "name": 1,
                    "pos": 1,
                    "quantiles": {0.1: 2.0, 0.25: 2.0, 0.5: 2.0, 0.75: 2.0, 0.9: 2.0},
                    "std": 0.0,
                    "zeros": 0,
                },
                2: {
                    "base_data_type": "numeric",
                    "count": 4,
                    "data_type": "int64",
                    "histogram": {
                        "(2.9968999999999997, 2.9976]": 0,
                        "(2.9976, 2.9982]": 0,
                        "(2.9982, 2.9988]": 0,
                        "(2.9988, 2.9994]": 0,
                        "(2.9994, 3.0]": 4,
                        "(3.0, 3.0006]": 0,
                        "(3.0006, 3.0012]": 0,
                        "(3.0012, 3.0018]": 0,
                        "(3.0018, 3.0024]": 0,
                        "(3.0024, 3.003]": 0,
                    },
                    "max": 3,
                    "mean": 3.0,
                    "min": 3,
                    "missing": 0,
                    "name": 2,
                    "pos": 2,
                    "quantiles": {0.1: 3.0, 0.25: 3.0, 0.5: 3.0, 0.75: 3.0, 0.9: 3.0},
                    "std": 0.0,
                    "zeros": 0,
                },
                3: {
                    "base_data_type": "numeric",
                    "count": 4,
                    "data_type": "int64",
                    "histogram": {
                        "(3.9959, 3.9968]": 0,
                        "(3.9968, 3.9976]": 0,
                        "(3.9976, 3.9984]": 0,
                        "(3.9984, 3.9992]": 0,
                        "(3.9992, 4.0]": 4,
                        "(4.0, 4.0008]": 0,
                        "(4.0008, 4.0016]": 0,
                        "(4.0016, 4.0024]": 0,
                        "(4.0024, 4.0032]": 0,
                        "(4.0032, 4.004]": 0,
                    },
                    "max": 4,
                    "mean": 4.0,
                    "min": 4,
                    "missing": 0,
                    "name": 3,
                    "pos": 3,
                    "quantiles": {0.1: 4.0, 0.25: 4.0, 0.5: 4.0, 0.75: 4.0, 0.9: 4.0},
                    "std": 0.0,
                    "zeros": 0,
                },
            },
        ),
        (
            np.ndarray([2, 2, 1]),
            create_node("test", np.ndarray),
            "unsupported",
            {
                "action": "reach out to the DAGWorks team to add " "support for this type.",
                "unsupported_type": "<class 'numpy.ndarray'> with " "dimensions (2, 2, 1)",
            },
        ),
        (
            [1, 2, 3, 4],
            create_node("test", list),
            "dict",  # yes dict to hack into the UI
            {"type": "<class 'list'>", "value": [1, 2, 3, 4]},
        ),
        (
            {"a": 1},
            create_node("test", dict),
            "dict",
            {"type": "<class 'dict'>", "value": {"a": 1}},
        ),
        (
            1,
            create_node("test", int),
            "primitive",
            {
                "type": "<class 'int'>",
                "value": 1,
            },
        ),
        (
            2.0,
            create_node("test", float),
            "primitive",
            {
                "type": "<class 'float'>",
                "value": 2.0,
            },
        ),
        (
            "3",
            create_node("test", str),
            "primitive",
            {
                "type": "<class 'str'>",
                "value": "3",
            },
        ),
        (
            False,
            create_node("test", bool),
            "primitive",
            {
                "type": "<class 'bool'>",
                "value": False,
            },
        ),
        (
            pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}),
            create_node("test", pl.DataFrame),
            "dagworks_describe",
            {
                "a": {
                    "count": 3,
                    "data_type": "Int64",
                    "histogram": {
                        "(-inf, 0.0]": 0,
                        "(0.0, 0.4]": 0,
                        "(0.4, 0.8]": 0,
                        "(0.8, 1.2]": 1,
                        "(1.2, 1.6]": 0,
                        "(1.6, 2.0]": 1,
                        "(2.0, 2.4]": 0,
                        "(2.4, 2.8]": 0,
                        "(2.8, 3.2]": 1,
                        "(3.2, 3.6]": 0,
                        "(3.6, inf]": 0,
                    },
                    "max": 3,
                    "mean": 2.0,
                    "min": 1,
                    "missing": 0,
                    "name": "a",
                    "pos": 0,
                    "quantiles": {0.1: 1.0, 0.25: 2.0, 0.5: 2.0, 0.75: 3.0, 0.9: 3.0},
                    "std": 1.0,
                    "zeros": 0,
                    "base_data_type": "numeric",
                },
                "b": {
                    "count": 3,
                    "data_type": "Int64",
                    "histogram": {
                        "(-inf, 3.0]": 0,
                        "(3.0, 3.4]": 0,
                        "(3.4, 3.8]": 0,
                        "(3.8, 4.2]": 1,
                        "(4.2, 4.6]": 0,
                        "(4.6, 5.0]": 1,
                        "(5.0, 5.4]": 0,
                        "(5.4, 5.8]": 0,
                        "(5.8, 6.2]": 1,
                        "(6.2, 6.6]": 0,
                        "(6.6, inf]": 0,
                    },
                    "max": 6,
                    "mean": 5.0,
                    "min": 4,
                    "missing": 0,
                    "name": "b",
                    "pos": 1,
                    "quantiles": {0.1: 4.0, 0.25: 5.0, 0.5: 5.0, 0.75: 6.0, 0.9: 6.0},
                    "std": 1.0,
                    "zeros": 0,
                    "base_data_type": "numeric",
                },
            },
        ),
        (
            pl.Series(values=[1, 2, 3], name="a"),
            create_node("a", pl.Series),
            "dagworks_describe",
            {
                "a": {
                    "count": 3,
                    "data_type": "Int64",
                    "histogram": {
                        "(-inf, 0.0]": 0,
                        "(0.0, 0.4]": 0,
                        "(0.4, 0.8]": 0,
                        "(0.8, 1.2]": 1,
                        "(1.2, 1.6]": 0,
                        "(1.6, 2.0]": 1,
                        "(2.0, 2.4]": 0,
                        "(2.4, 2.8]": 0,
                        "(2.8, 3.2]": 1,
                        "(3.2, 3.6]": 0,
                        "(3.6, inf]": 0,
                    },
                    "max": 3,
                    "mean": 2.0,
                    "min": 1,
                    "missing": 0,
                    "name": "a",
                    "pos": 0,
                    "quantiles": {0.1: 1.0, 0.25: 2.0, 0.5: 2.0, 0.75: 3.0, 0.9: 3.0},
                    "std": 1.0,
                    "zeros": 0,
                    "base_data_type": "numeric",
                }
            },
        ),
        (
            pl.Series(
                values=[None, None, None, None, None], name="a", dtype=pl.datatypes.classes.Float64
            ),
            create_node("a", pl.Series),
            "dagworks_describe",
            {
                "a": {
                    "count": 5,
                    "data_type": "Float64",
                    "histogram": {},
                    "max": None,
                    "mean": None,
                    "min": None,
                    "missing": 5,
                    "name": "a",
                    "pos": 0,
                    "quantiles": {0.1: None, 0.25: None, 0.5: None, 0.75: None, 0.9: None},
                    "std": None,
                    "zeros": 0,
                    "base_data_type": "numeric",
                }
            },
        ),
        (
            pl.date_range(date(2023, 1, 1), date(2023, 1, 3), eager=True).alias("a"),
            create_node("a", pl.Series),
            "dagworks_describe",  # TODO: fix quantiles
            {"a": {"base_data_type": "unknown-polars", "data_type": "Date", "name": "a", "pos": 0}},
        ),
    ],
    ids=[
        "pandas_df",
        "pandas_series",
        "nan_series",
        "datetime_series",
        "NaT_time_series",
        "numpy_array",
        "numpy_multid_array",
        "list",
        "dict",
        "int",
        "float",
        "str",
        "bool",
        "polars_df",
        "polars_series",
        "pl_nan_series",
        "pl_datetime_series",
    ],
)
def test_process_result_happy(test_result, test_node, observability_type, stats):
    """Tests a happy path for the process result function."""
    stats, schema, additional = runs.process_result(test_result, test_node)
    expected_result = result_base.copy()
    if observability_type in ["dict"]:
        expected_result["observability_schema_version"] = "0.0.2"
    if observability_type in ["primitive", "unsupported"]:
        expected_result["observability_schema_version"] = "0.0.1"
    expected_result["observability_type"] = observability_type
    expected_result["observability_value"] = stats["observability_value"]
    assert stats == expected_result
    # Allows us to double-check that everything can be json-dumped
    json.dumps(stats)
    # TODO -- test schema values, but probably not here
    if schema is not None:
        json.dumps(schema)
    [json.dumps(add) for add in additional]


def test_disable_capturing_data_stats(monkeypatch):
    monkeypatch.setattr("hamilton_sdk.tracking.constants.CAPTURE_DATA_STATISTICS", False)
    stats, schema, additional = runs.process_result([1, 2, 3, 4], create_node("a", list))
    assert stats["observability_type"] == "primitive"
    assert stats["observability_value"] == {
        "type": "str",
        "value": "RESULT SUMMARY DISABLED",
    }
