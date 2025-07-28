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

import collections
import typing

import numpy as np
import pandas as pd
import pytest
from numpy import testing
from packaging import version

from hamilton import base


def test_numpymatrixresult_int():
    """Tests the happy path of build_result of numpymatrixresult"""
    outputs = collections.OrderedDict(
        a=np.array([1, 7, 3, 7, 3, 6, 4, 9, 5, 0]), b=np.zeros(10), c=1
    )
    expected = np.array([[1, 7, 3, 7, 3, 6, 4, 9, 5, 0], np.zeros(10), np.ones(10)]).T
    actual = base.NumpyMatrixResult().build_result(**outputs)
    testing.assert_array_equal(actual, expected)


def test_numpymatrixresult_raise_length_mismatch():
    """Test raising an error build_result of numpymatrixresult"""
    outputs = collections.OrderedDict(
        a=np.array([1, 7, 3, 7, 3, 6, 4, 9, 5, 0]), b=np.array([1, 2, 3, 4, 5]), c=1
    )
    with pytest.raises(ValueError):
        base.NumpyMatrixResult().build_result(**outputs)


def test_SimplePythonGraphAdapter():
    """Tests that it delegates as intended"""

    class Foo(base.ResultMixin):
        @staticmethod
        def build_result(**outputs: typing.Dict[str, typing.Any]) -> typing.Any:
            outputs.update({"esoteric": "function"})
            return outputs

    spga = base.SimplePythonGraphAdapter(Foo())
    cols = {"a": "b"}
    expected = {"a": "b", "esoteric": "function"}
    actual = spga.build_result(**cols)
    assert actual == expected


def _gen_ints(n: int) -> typing.Iterator[int]:
    """Simple function to test that we can build results including generators."""
    yield from range(n)


class _Foo:
    """Dummy object used for testing."""

    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other: typing.Any) -> bool:
        return isinstance(other, _Foo) and other.name == self.name


@pytest.mark.parametrize(
    "outputs,expected_result",
    [
        ({"a": 1}, pd.DataFrame([{"a": 1}])),
        ({"a": pd.Series([1, 2, 3])}, pd.DataFrame({"a": pd.Series([1, 2, 3])})),
        (
            {"a": pd.DataFrame({"a": [1, 2, 3], "b": [11, 12, 13]})},
            pd.DataFrame({"a": pd.Series([1, 2, 3]), "b": pd.Series([11, 12, 13])}),
        ),
        ({"a": [1, 2, 3]}, pd.DataFrame({"a": [1, 2, 3]})),
        ({"a": np.array([1, 2, 3])}, pd.DataFrame({"a": pd.Series([1, 2, 3])})),
        ({"a": {"b": 1, "c": "foo"}}, pd.DataFrame({"a": {"b": 1, "c": "foo"}})),
        ({"a": _gen_ints(3)}, pd.DataFrame({"a": pd.Series([0, 1, 2])})),
        ({"a": _Foo("bar")}, pd.DataFrame([{"a": _Foo("bar")}])),
        ({"a": 1, "bar": 2}, pd.DataFrame([{"a": 1, "bar": 2}])),
        (
            {"a": pd.Series([1, 2, 3]), "b": pd.Series([11, 12, 13])},
            pd.DataFrame({"a": pd.Series([1, 2, 3]), "b": pd.Series([11, 12, 13])}),
        ),
        (
            {"a": pd.Series([1, 2, 3]), "b": pd.Series([11, 12, 13]), "c": 1},
            pd.DataFrame(
                {"a": pd.Series([1, 2, 3]), "b": pd.Series([11, 12, 13]), "c": pd.Series([1, 1, 1])}
            ),
        ),
        (
            {
                "a": pd.Series([1, 2, 3]),
                "b": pd.Series([11, 12, 13]),
                "c": pd.Series([11, 12, 13]).index,
            },
            pd.DataFrame(
                {"a": pd.Series([1, 2, 3]), "b": pd.Series([11, 12, 13]), "c": pd.Series([0, 1, 2])}
            ),
        ),
        (
            {"a": [1, 2, 3], "b": [4, 5, 6]},
            pd.DataFrame({"a": pd.Series([1, 2, 3]), "b": pd.Series([4, 5, 6])}),
        ),
        (
            {"a": np.array([1, 2, 3]), "b": np.array([4, 5, 6])},
            pd.DataFrame({"a": pd.Series([1, 2, 3]), "b": pd.Series([4, 5, 6])}),
        ),
        (
            {"a": {"b": 1, "c": "foo"}, "d": {"b": 2}},
            pd.DataFrame({"a": pd.Series({"b": 1, "c": "foo"}), "d": pd.Series({"b": 2})}),
        ),
        (
            {"a": _gen_ints(3), "b": _gen_ints(3)},
            pd.DataFrame({"a": pd.Series([0, 1, 2]), "b": pd.Series([0, 1, 2])}),
        ),
        (
            {"a": pd.Series([1, 2, 3]), "b": 4},
            pd.DataFrame({"a": pd.Series([1, 2, 3]), "b": pd.Series([4, 4, 4])}),
        ),
        (
            {"a": [1, 2, 3], "b": 4},
            pd.DataFrame({"a": pd.Series([1, 2, 3]), "b": pd.Series([4, 4, 4])}),
        ),
        (
            {
                "a": {
                    "bar": 2,
                    "foo": 1,
                },
                "b": 4,
            },
            pd.DataFrame({"a": pd.Series([2, 1]), "b": pd.Series([4, 4])}).rename(
                index=lambda i: ["bar", "foo"][i]
            ),
        ),
        (
            {"a": pd.Series([1, 2, 3]), "b": pd.Series([4, 5, 6])},
            pd.DataFrame({"a": pd.Series([1, 2, 3]), "b": pd.Series([4, 5, 6])}),
        ),
        (
            {
                "a": pd.DataFrame({"a": [1, 2, 3], "b": [11, 12, 13]}),
                "b": pd.DataFrame({"c": [1, 3, 5], "d": [14, 15, 16]}),
            },
            pd.DataFrame(
                {"a.a": [1, 2, 3], "a.b": [11, 12, 13], "b.c": [1, 3, 5], "b.d": [14, 15, 16]}
            ),
        ),
        (
            {
                "a": pd.Series([1, 2, 3]),
                "b": pd.Series([11, 12, 13]),
                "c": pd.DataFrame({"d": [0, 0, 0]}),
            },
            pd.DataFrame(
                {"a": pd.Series([1, 2, 3]), "b": pd.Series([11, 12, 13]), "c.d": [0, 0, 0]}
            ),
        ),
    ],
    ids=[
        "test-single-scalar",
        "test-single-series",
        "test-single-dataframe",
        "test-single-list",
        "test-single-array",
        "test-single-dict",
        "test-single-generator",
        "test-single-object",
        "test-multiple-scalars",
        "test-multiple-series",
        "test-multiple-series-with-scalar",
        "test-multiple-series-with-index",
        "test-multiple-lists",
        "test-multiple-arrays",
        "test-multiple-dicts",
        "test-multiple-generators",
        "test-scalar-and-series",
        "test-scalar-and-list",
        "test-scalar-and-dict",
        "test-series-and-list",
        "test-multiple-dataframes",
        "test-multiple-series-with-dataframe",
    ],
)
def test_PandasDataFrameResult_build_result(outputs, expected_result):
    """Tests the happy case of PandasDataFrameResult.build_result()"""
    pdfr = base.PandasDataFrameResult()
    actual = pdfr.build_result(**outputs)
    pd.testing.assert_frame_equal(actual, expected_result)


@pytest.mark.parametrize(
    "outputs",
    [
        ({"a": [1, 2], "b": {"foo": "bar"}}),
        ({"a": [1, 2], "b": [3, 4, 5]}),
        ({"a": np.array([1, 2]), "b": np.array([3, 4, 5])}),
        ({"a": _gen_ints(3), "b": _gen_ints(4)}),
    ],
    ids=[
        "test-lists-and-dicts",
        "test-mismatched-lists",
        "test-mismatched-arrays",
        "test-mismatched-generators",
    ],
)
def test_PandasDataFrameResult_build_result_errors(outputs):
    """Tests the error case of PandasDataFrameResult.build_result()"""
    pdfr = base.PandasDataFrameResult()
    with pytest.raises(ValueError):
        pdfr.build_result(**outputs)


@pytest.mark.parametrize(
    "outputs,expected_result",
    [
        (
            {
                "a": pd.DataFrame({"a": [1, 2, 3], "z": [0, 0, 0]}),
                "b": pd.Series([4, 5, 6]),
                "c": 7,
                "d": [8, 9, 10],
            },
            pd.DataFrame(
                {
                    "a.a": [1, 2, 3],
                    "a.z": [0, 0, 0],
                    "b": [4, 5, 6],
                    "c": [7, 7, 7],
                    "d": [8, 9, 10],
                }
            ),
        ),
        (
            {
                "a": pd.DataFrame({"a": [1, 2, 3], "b": [11, 12, 13]}, index=[0, 1, 2]),
                "b": pd.DataFrame({"c": [1, 3, 5], "d": [14, 15, 16]}, index=[3, 4, 5]),
            },
            pd.DataFrame(
                {
                    "a.a": [1, 2, 3, None, None, None],
                    "a.b": [11, 12, 13, None, None, None],
                    "b.c": [None, None, None, 1, 3, 5],
                    "b.d": [None, None, None, 14, 15, 16],
                },
                index=[0, 1, 2, 3, 4, 5],
            ),
        ),
        (
            {
                "a": pd.Series([1, 2, 3], index=[1, 2, 3]),
                "c": pd.DataFrame({"d": [0, 0, 0], "e": [1, 1, 1]}),
                "b": pd.Series([11, 12, 13]),
                "f": pd.DataFrame({"g": [2, 2, 2], "h": [3, 3, 3]}, index=[1, 2, 3]),
            },
            pd.DataFrame(
                {
                    "a": [None, 1, 2, 3],
                    "c.d": [0, 0, 0, None],
                    "c.e": [1, 1, 1, None],
                    "b": [11, 12, 13, None],
                    "f.g": [None, 2, 2, 2],
                    "f.h": [None, 3, 3, 3],
                },
                index=[0, 1, 2, 3],
            ),
        ),
    ],
    ids=[
        "test-dataframe-scalar-series-list",
        "test-two-dataframes",
        "test-order-and-outer-join-preserved",
    ],
)
def test_PandasDataFrameResult_build_dataframe_with_dataframes(outputs, expected_result):
    """Tests build_dataframe_with_dataframes errors as expected"""
    pdfr = base.PandasDataFrameResult()
    actual = pdfr.build_dataframe_with_dataframes(outputs)
    pd.testing.assert_frame_equal(actual, expected_result)


# Still supporting old pandas version, although we should phase off...
int_64_index = "Index:::int64" if pd.__version__ >= "2.0.0" else "RangeIndex:::int64"

PD_VERSION = version.parse(pd.__version__)


@pytest.mark.parametrize(
    "outputs,expected_result",
    [
        ({"a": pd.Series([1, 2, 3])}, ({"RangeIndex:::int64": ["a"]}, {}, {})),
        (
            {"a": pd.Series([1, 2, 3]), "b": pd.Series([3, 4, 5])},
            ({"RangeIndex:::int64": ["a", "b"]}, {}, {}),
        ),
        (
            {
                "b": pd.Series(
                    [3, 4, 5], index=pd.DatetimeIndex(["2022-01", "2022-02", "2022-03"], freq="MS")
                )
            },
            (
                {"DatetimeIndex:::datetime64[ns]": ["b"]},
                {"DatetimeIndex:::datetime64[ns]": ["b"]},
                {},
            ),
        ),
        ({"c": 1}, ({"no-index": ["c"]}, {}, {"no-index": ["c"]})),
        (
            {
                "a": pd.Series([1, 2, 3]),
                "b": 1,
                "c": pd.Series(
                    [3, 4, 5], index=pd.DatetimeIndex(["2022-01", "2022-02", "2022-03"], freq="MS")
                ),
            },
            (
                {
                    "DatetimeIndex:::datetime64[ns]": ["c"],
                    "RangeIndex:::int64": ["a"],
                    "no-index": ["b"],
                },
                {"DatetimeIndex:::datetime64[ns]": ["c"]},
                {"no-index": ["b"]},
            ),
        ),
        ({"a": pd.DataFrame({"a": [1, 2, 3]})}, ({"RangeIndex:::int64": ["a"]}, {}, {})),
        pytest.param(
            {"a": pd.Series([1, 2, 3]).index},
            ({"Index:::int64": ["a"]}, {}, {}),
            marks=pytest.mark.skipif(
                PD_VERSION < version.parse("2.0.0"),
                reason="Pandas 2.0 changed default indices but we still " "support pandas <2.0",
            ),
        ),
        pytest.param(
            {"a": pd.Series([1, 2, 3]).index},
            ({"Int64Index:::int64": ["a"]}, {}, {}),
            marks=pytest.mark.skipif(
                PD_VERSION >= version.parse("2.0.0"),
                reason="Pandas 2.0 changed default indices but we still " "support pandas <2.0",
            ),
        ),
    ],
    ids=[
        "int-index",
        "int-index-double",
        "ts-index",
        "no-index",
        "multiple-different-indexes",
        "df-index",
        "index-object-3-7",
        "index-object-3-8-plus",
    ],
)
def test_PandasDataFrameResult_pandas_index_types(outputs, expected_result):
    """Tests exercising the function to return pandas index types from outputs"""
    pdfr = base.PandasDataFrameResult()
    actual = pdfr.pandas_index_types(outputs)
    assert dict(actual[0]) == expected_result[0]
    assert dict(actual[1]) == expected_result[1]
    assert dict(actual[2]) == expected_result[2]


@pytest.mark.parametrize(
    "all_index_types,time_indexes,no_indexes,expected_result",
    [
        ({"foo": ["a", "b", "c"]}, {}, {}, True),
        ({"int-index": ["a"], "no-index": ["b"]}, {}, {"no-index": ["b"]}, True),
        ({"ts-1": ["a"], "ts-2": ["b"]}, {"ts-1": ["a"], "ts-2": ["b"]}, {}, False),
        ({"float-index": ["a"], "int-index": ["b"]}, {}, {}, False),
        ({"no-index": ["a", "b"]}, {}, {"no-index": ["a", "b"]}, False),
    ],
    ids=[
        "all-the-same",  # True
        "single-index-with-no-index",  # True
        "multiple-ts",  # False
        "multiple-indexes-not-ts",  # False
        "no-indexes-at-all",  # False4
    ],
)
def test_PandasDataFrameResult_check_pandas_index_types_match(
    all_index_types, time_indexes, no_indexes, expected_result
):
    """Tests exercising the function to determine whether pandas index types match"""
    # setup to test conditional if statement on logger level
    import logging

    logger = logging.getLogger("hamilton.base")  # get logger of base module.
    logger.setLevel(logging.DEBUG)
    pdfr = base.PandasDataFrameResult()
    actual = pdfr.check_pandas_index_types_match(all_index_types, time_indexes, no_indexes)
    assert actual == expected_result


@pytest.mark.parametrize(
    "outputs,expected_result",
    [
        ({"a": pd.Series([1, 2, 3])}, pd.DataFrame({"a": pd.Series([1, 2, 3])})),
        (
            {
                "a": pd.Series(
                    [1, 2, 3], index=pd.DatetimeIndex(["2022-01", "2022-02", "2022-03"], freq="MS")
                ),
                "b": pd.Series(
                    [3, 4, 5], index=pd.DatetimeIndex(["2022-01", "2022-02", "2022-03"], freq="MS")
                ),
            },
            pd.DataFrame(
                {
                    "a": pd.Series(
                        [1, 2, 3],
                        index=pd.DatetimeIndex(["2022-01", "2022-02", "2022-03"], freq="MS"),
                    ),
                    "b": pd.Series(
                        [3, 4, 5],
                        index=pd.DatetimeIndex(["2022-01", "2022-02", "2022-03"], freq="MS"),
                    ),
                }
            ),
        ),
        (
            {
                "a": pd.Series(
                    [1, 2, 3], index=pd.DatetimeIndex(["2022-01", "2022-02", "2022-03"], freq="MS")
                ),
                "b": 4,
            },
            pd.DataFrame(
                {
                    "a": pd.Series(
                        [1, 2, 3],
                        index=pd.DatetimeIndex(["2022-01", "2022-02", "2022-03"], freq="MS"),
                    ),
                    "b": 4,
                }
            ),
        ),
    ],
    ids=[
        "test-same-index-simple",
        "test-same-index-ts",
        "test-index-with-scalar",
    ],
)
def test_StrictIndexTypePandasDataFrameResult_build_result(outputs, expected_result):
    """Tests the happy case of StrictIndexTypePandasDataFrameResult.build_result()"""
    sitpdfr = base.StrictIndexTypePandasDataFrameResult()
    actual = sitpdfr.build_result(**outputs)
    pd.testing.assert_frame_equal(actual, expected_result)


@pytest.mark.parametrize(
    "outputs",
    [
        (
            {
                "a": pd.Series([1, 2, 3], index=[0, 1, 2]),
                "b": pd.Series([1, 2, 3], index=[0.0, 1.0, 2.0]),
            }
        ),
        (
            {
                "series1": pd.Series(
                    [1, 2, 3], index=pd.DatetimeIndex(["2022-01", "2022-02", "2022-03"], freq="MS")
                ),
                "series2": pd.Series(
                    [4, 5, 6],
                    index=pd.PeriodIndex(year=[2022, 2022, 2022], month=[1, 2, 3], freq="M"),
                ),
                "series3": pd.Series(
                    [4, 5, 6],
                    index=pd.PeriodIndex(
                        year=[2022, 2022, 2022], month=[1, 1, 1], day=[3, 4, 5], freq="B"
                    ),
                ),
                "series4": pd.Series(
                    [4, 5, 6],
                    index=pd.PeriodIndex(
                        year=[2022, 2022, 2022], month=[1, 1, 1], day=[4, 11, 18], freq="W"
                    ),
                ),
            }
        ),
    ],
    ids=[
        "test-int-float",
        "test-different-ts-indexes",
    ],
)
def test_StrictIndexTypePandasDataFrameResult_build_result_errors(outputs):
    """Tests the error case of StrictIndexTypePandasDataFrameResult.build_result()"""
    sitpdfr = base.StrictIndexTypePandasDataFrameResult()
    with pytest.raises(ValueError):
        sitpdfr.build_result(**outputs)
