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
from hamilton_sdk.tracking import pandas_stats as ps


def test_compute_stats_df():
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
            "i": pd.Series([None, None, None, None, None], name="a", dtype=float),
            "j": pd.Series(name="a", data=pd.date_range("20230101", "20230105")),
        }
    )
    actual = ps.compute_stats_df(df, "test", {})
    expected_stats = {
        "observability_schema_version": "0.0.3",
        "observability_type": "dagworks_describe",
        "observability_value": {
            "a": {
                "base_data_type": "numeric",
                "count": 5,
                "data_type": "int64",
                "histogram": {
                    "(0.995, 1.4]": 1,
                    "(1.4, 1.8]": 0,
                    "(1.8, 2.2]": 1,
                    "(2.2, 2.6]": 0,
                    "(2.6, 3.0]": 1,
                    "(3.0, 3.4]": 0,
                    "(3.4, 3.8]": 0,
                    "(3.8, 4.2]": 1,
                    "(4.2, 4.6]": 0,
                    "(4.6, 5.0]": 1,
                },
                "max": 5,
                "mean": 3.0,
                "min": 1,
                "missing": 0,
                "name": "a",
                "pos": 0,
                "quantiles": {0.1: 1.4, 0.25: 2.0, 0.5: 3.0, 0.75: 4.0, 0.9: 4.6},
                "std": 1.5811388300841898,
                "zeros": 0,
            },
            "b": {
                "base_data_type": "unhandled",
                "count": 5,
                "data_type": "object",
                "missing": 0,
                "name": "b",
                "pos": 1,
            },
            "c": {
                "base_data_type": "boolean",
                "count": 5,
                "data_type": "bool",
                "missing": 0,
                "name": "c",
                "pos": 2,
                "zeros": 2,
            },
            "d": {
                "base_data_type": "numeric",
                "count": 5,
                "data_type": "float64",
                "histogram": {
                    "(0.995, 1.4]": 1,
                    "(1.4, 1.8]": 0,
                    "(1.8, 2.2]": 1,
                    "(2.2, 2.6]": 0,
                    "(2.6, 3.0]": 1,
                    "(3.0, 3.4]": 0,
                    "(3.4, 3.8]": 0,
                    "(3.8, 4.2]": 1,
                    "(4.2, 4.6]": 0,
                    "(4.6, 5.0]": 1,
                },
                "max": 5.0,
                "mean": 3.0,
                "min": 1.0,
                "missing": 0,
                "name": "d",
                "pos": 3,
                "quantiles": {0.1: 1.4, 0.25: 2.0, 0.5: 3.0, 0.75: 4.0, 0.9: 4.6},
                "std": 1.5811388300841898,
                "zeros": 0,
            },
            "e": {
                "base_data_type": "category",
                "count": 5,
                "data_type": "category",
                "domain": {"a": 1, "b": 1, "c": 1, "d": 1, "e": 1},
                "empty": 0,
                "missing": 0,
                "name": "e",
                "pos": 4,
                "top_freq": 1,
                "top_value": "a",
                "unique": 5,
            },
            "f": {
                "avg_str_len": 1.0,
                "base_data_type": "str",
                "count": 5,
                "data_type": "string",
                "empty": 0,
                "missing": 0,
                "name": "f",
                "pos": 5,
                "std_str_len": 0.0,
            },
            "g": {
                "base_data_type": "unhandled",
                "count": 5,
                "data_type": "object",
                "missing": 0,
                "name": "g",
                "pos": 6,
            },
            "h": {
                "base_data_type": "datetime",
                "count": 5,
                "data_type": "datetime64[ns]",
                "histogram": {
                    "(2022-12-30 23:59:58.999999999, 2022-12-30 23:59:59.200000]": 0,
                    "(2022-12-30 23:59:59.200000, 2022-12-30 23:59:59.400000]": 0,
                    "(2022-12-30 23:59:59.400000, 2022-12-30 23:59:59.600000]": 0,
                    "(2022-12-30 23:59:59.600000, 2022-12-30 23:59:59.800000]": 0,
                    "(2022-12-30 23:59:59.800000, 2022-12-31 00:00:00]": 4,
                    "(2022-12-31 00:00:00, 2022-12-31 00:00:00.200000]": 0,
                    "(2022-12-31 00:00:00.200000, 2022-12-31 00:00:00.400000]": 0,
                    "(2022-12-31 00:00:00.400000, 2022-12-31 00:00:00.600000]": 0,
                    "(2022-12-31 00:00:00.600000, 2022-12-31 00:00:00.800000]": 0,
                    "(2022-12-31 00:00:00.800000, 2022-12-31 00:00:01]": 0,
                },
                "max": "2022-12-31T00:00:00",
                "mean": "2022-12-31T00:00:00",
                "min": "2022-12-31T00:00:00",
                "missing": 1,
                "name": "h",
                "pos": 7,
                "quantiles": {
                    0.1: "2022-12-31T00:00:00",
                    0.25: "2022-12-31T00:00:00",
                    0.5: "2022-12-31T00:00:00",
                    0.75: "2022-12-31T00:00:00",
                    0.9: "2022-12-31T00:00:00",
                },
                "std": "P0DT0H0M0S",
                "zeros": 0,
            },
            "i": {
                "base_data_type": "numeric",
                "count": 5,
                "data_type": "float64",
                "histogram": {},
                "max": None,
                "mean": None,
                "min": None,
                "missing": 5,
                "name": "i",
                "pos": 8,
                "quantiles": {0.1: None, 0.25: None, 0.5: None, 0.75: None, 0.9: None},
                "std": None,
                "zeros": 0,
            },
            "j": {
                "base_data_type": "datetime",
                "count": 5,
                "data_type": "datetime64[ns]",
                "histogram": {
                    "(2022-12-31 23:54:14.399999999, 2023-01-01 09:36:00]": 1,
                    "(2023-01-01 09:36:00, 2023-01-01 19:12:00]": 0,
                    "(2023-01-01 19:12:00, 2023-01-02 04:48:00]": 1,
                    "(2023-01-02 04:48:00, 2023-01-02 14:24:00]": 0,
                    "(2023-01-02 14:24:00, 2023-01-03 00:00:00]": 1,
                    "(2023-01-03 00:00:00, 2023-01-03 09:36:00]": 0,
                    "(2023-01-03 09:36:00, 2023-01-03 19:12:00]": 0,
                    "(2023-01-03 19:12:00, 2023-01-04 04:48:00]": 1,
                    "(2023-01-04 04:48:00, 2023-01-04 14:24:00]": 0,
                    "(2023-01-04 14:24:00, 2023-01-05 00:00:00]": 1,
                },
                "max": "2023-01-05T00:00:00",
                "mean": "2023-01-03T00:00:00",
                "min": "2023-01-01T00:00:00",
                "missing": 0,
                "name": "j",
                "pos": 9,
                "quantiles": {
                    0.1: "2023-01-01T09:36:00",
                    0.25: "2023-01-02T00:00:00",
                    0.5: "2023-01-03T00:00:00",
                    0.75: "2023-01-04T00:00:00",
                    0.9: "2023-01-04T14:24:00",
                },
                "std": "P1DT13H56M50.394919273S",
                "zeros": 0,
            },
        },
    }
    assert actual == expected_stats
