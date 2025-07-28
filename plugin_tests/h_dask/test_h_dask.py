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

import typing

import dask.dataframe as dd
import numpy as np
import pandas as pd
import pytest
from dask.delayed import delayed
from distributed import Client

from hamilton import driver
from hamilton.plugins import h_dask

from .resources import example_module, smoke_screen_module


@pytest.fixture(scope="session")
def client():
    with Client(set_as_default=False).as_current() as client:
        yield client


def test_dask_graph_adapter_simple(client):
    initial_columns = {
        # NOTE: here you could load individual columns from a parquet file
        # in delayed manner, e.g., using sth. along the lines of
        #     delayed(lambda: pd.read_parquet(path, columns=[col])[col])()
        "signups": delayed(lambda: pd.Series([1, 10, 50, 100, 200, 400]))(),
        "spend": delayed(lambda: pd.Series([10, 10, 20, 40, 40, 50]))(),
    }

    dr = driver.Driver(initial_columns, example_module, adapter=h_dask.DaskGraphAdapter(client))

    output_columns = [
        "spend",
        "signups",
        "avg_3wk_spend",
        "spend_per_signup",
    ]
    df = dr.execute(output_columns)

    assert set(df) == set(output_columns)
    expected_column = pd.Series(
        [0.0, 0.0, 13.33333, 23.33333, 33.33333, 43.33333], name="avg_3wk_spend"
    )
    pd.testing.assert_series_equal(
        df.avg_3wk_spend.fillna(0.0), expected_column
    )  # fill na to get around NaN
    # TODO: do some more asserting?


def test_smoke_screen_module(client):
    config = {"region": "US"}
    dr = driver.Driver(config, smoke_screen_module, adapter=h_dask.DaskGraphAdapter(client))
    output_columns = [
        "raw_acquisition_cost",
        "pessimistic_net_acquisition_cost",
        "neutral_net_acquisition_cost",
        "optimistic_net_acquisition_cost",
        "series_with_start_date_end_date",
    ]
    df = dr.execute(
        inputs={"date_range": {"start_date": "20200101", "end_date": "20220801"}},
        final_vars=output_columns,
    )
    epsilon = 0.00001
    assert abs(df["raw_acquisition_cost"].mean() - 0.393808) < epsilon
    assert abs(df["pessimistic_net_acquisition_cost"].mean() - 0.420769) < epsilon
    assert abs(df["neutral_net_acquisition_cost"].mean() - 0.405582) < epsilon
    assert abs(df["optimistic_net_acquisition_cost"].mean() - 0.399363) < epsilon
    assert df["series_with_start_date_end_date"].iloc[0] == "date_20200101_date_20220801"


# The following tests are for exercising the DaskDataFrameResult.build_result function
dd_test_cases = [
    # single_scalar
    ({"a": 1}, pd.DataFrame({"a": [1]})),
    # single_series
    ({"a": pd.Series([1, 2, 3])}, pd.DataFrame({"a": [1, 2, 3]})),
    # single_dataframe
    ({"a": pd.DataFrame({"a": [1, 2, 3]})}, pd.DataFrame({"a.a": [1, 2, 3]})),
    # multiple_series
    (
        {"a": pd.Series([1, 2, 3]), "b": pd.Series([4, 5, 6])},
        pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}),
    ),
    # multiple_dataframe
    (
        {"a": pd.DataFrame({"a": [1, 2, 3]}), "b": pd.DataFrame({"b": [4, 5, 6]})},
        pd.DataFrame({"a.a": [1, 2, 3], "b.b": [4, 5, 6]}),
    ),
    # series_and_dataframe
    (
        {"a": pd.Series([1, 2, 3]), "b": pd.DataFrame({"b": [4, 5, 6]})},
        pd.DataFrame({"a": [1, 2, 3], "b.b": [4, 5, 6]}),
    ),
    # series_and_scalar
    (
        {"b": pd.Series([4, 5, 6]), "a": 1, "c": "string"},
        pd.DataFrame({"b": [4, 5, 6], "a": [1, 1, 1], "c": ["string", "string", "string"]}),
    ),
    # dataframe_and_scalar
    (
        {"a": pd.DataFrame({"a": [1, 2, 3]}), "b": 1},
        pd.DataFrame({"a.a": [1, 2, 3], "b": [1, 1, 1]}),
    ),
    # dataframe_and_series
    (
        {
            "a": pd.Series([1, 2, 3]),
            "b": pd.DataFrame({"b": [1, 2, 3], "c": [1, 1, 1]}),
        },
        pd.DataFrame({"a": [1, 2, 3], "b.b": [1, 2, 3], "b.c": [1, 1, 1]}),
    ),
    # multiple_series_and_scalar
    (
        {"a": pd.Series([1, 2, 3]), "b": pd.Series([4, 5, 6]), "c": 12},
        pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [12, 12, 12]}),
    ),
    # multiple_dataframes_and_scalar
    (
        {
            "a": pd.DataFrame({"a": [1, 2, 3]}),
            "b": pd.DataFrame({"b": [4, 5, 6], "d": [2, 2, 2]}),
            "c": 12,
        },
        pd.DataFrame({"a.a": [1, 2, 3], "b.b": [4, 5, 6], "b.d": [2, 2, 2], "c": [12, 12, 12]}),
    ),
    # multiple_series_and_dataframe
    (
        {
            "d": pd.Series([11, 22, 33]),
            "e": pd.Series([44, 55, 66]),
            "c": pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}),
        },
        pd.DataFrame(
            {
                "d": [11, 22, 33],
                "e": [44, 55, 66],
                "c.a": [1, 2, 3],
                "c.b": [4, 5, 6],
            }
        ),
    ),
    # multiple_series_and_dataframe_and_scalar
    (
        {
            "d": pd.Series([11, 22, 33]),
            "e": pd.Series([44, 55, 66]),
            "c": pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}),
            "f": 12,
        },
        pd.DataFrame(
            {
                "d": [11, 22, 33],
                "e": [44, 55, 66],
                "c.a": [1, 2, 3],
                "c.b": [4, 5, 6],
                "f": [12, 12, 12],
            }
        ),
    ),
    # numpy_arrays
    (
        {"a": np.array([1, 2, 3]), "b": np.array([4, 5, 6])},
        pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}),
    ),
    # lists
    ({"a": [1, 2, 3], "b": [4, 5, 6]}, pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})),
    # tuples
    ({"a": (1, 2, 3), "b": (4, 5, 6)}, pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})),
]
dd_test_case_ids = [
    "single_scalar",
    "single_series",
    "single_dataframe",
    "multiple_series",
    "multiple_dataframes",
    "series_and_dataframe",
    "series_and_scalar",
    "dataframe_and_scalar",
    "dataframe_and_series",
    "multiple_series_and_scalar",
    "multiple_dataframes_and_scalar",
    "multiple_series_and_dataframe",
    "multiple_series_and_dataframe_and_scalar",
    "numpy_arrays",
    "lists",
    "tuples",
]


@pytest.mark.parametrize("outputs, expected", dd_test_cases, ids=dd_test_case_ids)
def test_DDFR_build_result_pandas(
    client, outputs: typing.Dict[str, typing.Any], expected: dd.DataFrame
):
    """Tests using pandas objects works"""
    actual = h_dask.DaskDataFrameResult.build_result(**outputs)
    actual_pdf = actual.compute().convert_dtypes(dtype_backend="pyarrow")
    expected_pdf = expected.convert_dtypes(dtype_backend="pyarrow")
    pd.testing.assert_frame_equal(actual_pdf, expected_pdf)


@pytest.mark.parametrize("outputs, expected", dd_test_cases, ids=dd_test_case_ids)
def test_DDFR_build_result_dask(
    client, outputs: typing.Dict[str, typing.Any], expected: dd.DataFrame
):
    """Tests that using dask objects works."""
    dask_outputs = {}
    for k, v in outputs.items():
        if isinstance(v, (pd.DataFrame, pd.Series)):
            dask_outputs[k] = dd.from_pandas(v, npartitions=2)
        else:
            dask_outputs[k] = v
    actual = h_dask.DaskDataFrameResult.build_result(**dask_outputs)
    actual_pdf = actual.compute().convert_dtypes(dtype_backend="pyarrow")
    expected_pdf = expected.convert_dtypes(dtype_backend="pyarrow")
    pd.testing.assert_frame_equal(actual_pdf, expected_pdf)


def test_DDFR_build_result_mixed(client):
    """Tests that using dask & pandas objects works."""
    outputs = {
        "d": dd.from_pandas(pd.Series([11, 22, 33]), npartitions=2),
        "e": pd.Series([44, 55, 66]),
        "c": pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}),
        "g": dd.from_pandas(pd.DataFrame({"a2": [1, 2, 3], "b2": [4, 5, 6]}), npartitions=2),
        "f": 12,
    }
    expected_df = pd.DataFrame(
        {
            "d": [11, 22, 33],
            "e": [44, 55, 66],
            "c.a": [1, 2, 3],
            "c.b": [4, 5, 6],
            "g.a2": [1, 2, 3],
            "g.b2": [4, 5, 6],
            "f": [12, 12, 12],
        }
    )
    actual = h_dask.DaskDataFrameResult.build_result(**outputs)
    actual_pdf = actual.compute().convert_dtypes(dtype_backend="pyarrow")
    expected_pdf = expected_df.convert_dtypes(dtype_backend="pyarrow")
    pd.testing.assert_frame_equal(actual_pdf, expected_pdf)


def test_DDFR_build_result_scalar_first_edge_case(client):
    """Tests the scalar edge case where we don't know how long to make the series from it."""
    actual = h_dask.DaskDataFrameResult.build_result(
        **{"a": 1, "b": dd.from_pandas(pd.Series([4, 5, 6]), npartitions=1)}
    )
    expected = pd.DataFrame({"a": [1, pd.NA, pd.NA], "b": [4, 5, 6]})
    actual_pdf = actual.compute().convert_dtypes(dtype_backend="pyarrow")
    expected_pdf = expected.convert_dtypes(dtype_backend="pyarrow")
    pd.testing.assert_frame_equal(actual_pdf, expected_pdf)


def test_DDFR_build_result_varied_index_lengths(client):
    """Tests what happens when the index lengths are different.

    So this test enshrines the current logic of how we handle scalars and series/dfs with different
    lengths. We could do smarter things here (e.g. make scalars=max(len(...))), but this is the current behavior.

    Our thinking is that you should control this via the order of the outputs requested for now.
    i.e. re-arranging the outputs dictionary should give you the desired result that you want.
    """
    outputs = {
        "a": 1,
        "b": dd.from_pandas(pd.Series([4, 5, 6]), npartitions=1),
        "c": dd.from_pandas(pd.Series([10, 6]), npartitions=1),
        "d": pd.DataFrame({"a": [11, 22, 33, 44], "b": [44, 55, 66, 77]}),
        "e": "a",
    }
    actual = h_dask.DaskDataFrameResult.build_result(**outputs)
    expected = pd.DataFrame(
        {
            "a": [1, pd.NA, pd.NA, pd.NA],
            "b": [4, 5, 6, pd.NA],
            "c": [10, 6, pd.NA, pd.NA],
            "d.a": [11, 22, 33, 44],
            "d.b": [44, 55, 66, 77],
            "e": ["a", "a", "a", pd.NA],
        }
    )
    actual_pdf = actual.compute().convert_dtypes(dtype_backend="pyarrow")
    expected_pdf = expected.convert_dtypes(dtype_backend="pyarrow")
    pd.testing.assert_frame_equal(actual_pdf, expected_pdf)


def test_DDFR_build_result_dd_scalar(client):
    """Tests that dask scalars work as expected."""
    outputs = {
        "a": dd.from_pandas(pd.Series([4, 5, 6]), npartitions=1),
        "b": dd.from_pandas(pd.Series([10, 6, 3]), npartitions=1),
    }
    outputs["c"] = outputs["a"].sum()
    actual = h_dask.DaskDataFrameResult.build_result(**outputs)
    expected = pd.DataFrame(
        {
            "a": [4, 5, 6],
            "b": [10, 6, 3],
            "c": [15, 15, 15],
        }
    )
    actual_pdf = actual.compute().convert_dtypes(dtype_backend="pyarrow")
    expected_pdf = expected.convert_dtypes(dtype_backend="pyarrow")
    pd.testing.assert_frame_equal(actual_pdf, expected_pdf)
