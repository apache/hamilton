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

import sys

import numpy as np
import pandas as pd
import pyspark.pandas as ps
import pytest
from pyspark import Row
from pyspark.sql import Column, DataFrame, SparkSession, types
from pyspark.sql.connect.session import SparkSession as CSparkSession
from pyspark.sql.functions import column

from hamilton import base, driver, htypes, node
from hamilton.function_modifiers.base import NodeInjector
from hamilton.function_modifiers.recursive import prune_nodes
from hamilton.plugins import h_spark
from hamilton.plugins.h_spark import SparkInputValidator

from .resources import example_module, smoke_screen_module
from .resources.spark import (
    basic_spark_dag,
    pyspark_udfs,
    spark_dag_external_dependencies,
    spark_dag_mixed_pyspark_pandas_udfs,
    spark_dag_multiple_with_columns,
    spark_dag_pyspark_udfs,
)
from tests.resources.spark import a_dag


@pytest.fixture(scope="module")
def spark_session():
    spark = (
        SparkSession.builder.master("local")
        .appName("spark session")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )
    yield spark
    spark.stop()


def test_koalas_spark_graph_adapter(spark_session):
    initial_columns = {
        "signups": ps.Series([1, 10, 50, 100, 200, 400], name="signups"),
        "spend": ps.Series([10, 10, 20, 40, 40, 50], name="signups"),
    }
    ps.set_option(
        "compute.ops_on_diff_frames", True
    )  # we should play around here on how to correctly initialize data.
    ps.set_option("compute.default_index_type", "distributed")  # this one doesn't seem to work?
    dr = driver.Driver(
        initial_columns,
        example_module,
        adapter=h_spark.SparkKoalasGraphAdapter(
            spark_session,
            result_builder=base.PandasDataFrameResult(),
            spine_column="spend",
        ),
    )
    output_columns = [
        "spend",
        "signups",
        "avg_3wk_spend",
        "spend_per_signup",
    ]
    df = dr.execute(output_columns)
    assert set(df) == set(output_columns)
    expected_column = pd.Series(
        [0.0, 0.0, 13.33333, 23.33333, 33.33333, 43.33333],
        index=[0, 1, 2, 3, 4, 5],
        name="avg_3wk_spend",
    )
    pd.testing.assert_series_equal(
        df.avg_3wk_spend.fillna(0.0).sort_index(), expected_column
    )  # fill na to get around NaN
    # TODO: do some more asserting?


def test_smoke_screen_module(spark_session):
    config = {"region": "US", "pandas_on_spark": True}
    ps.set_option(
        "compute.ops_on_diff_frames", True
    )  # we should play around here on how to correctly initialize data.
    ps.set_option("compute.default_index_type", "distributed")  # this one doesn't seem to work?
    dr = driver.Driver(
        config,
        smoke_screen_module,
        adapter=h_spark.SparkKoalasGraphAdapter(
            spark_session,
            result_builder=base.PandasDataFrameResult(),
            spine_column="weeks",
        ),
    )
    output_columns = [
        "raw_acquisition_cost",
        "pessimistic_net_acquisition_cost",
        "neutral_net_acquisition_cost",
        "optimistic_net_acquisition_cost",
        "weeks",
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


@pytest.mark.parametrize(
    "input_and_expected_fn",
    [
        (lambda df: ({}, (None, {}))),
        (lambda df: ({"a": 1}, (None, {"a": 1}))),
        (lambda df: ({"a": df}, (df, {}))),
        (lambda df: ({"a": df, "b": 1}, (df, {"b": 1}))),
    ],
    ids=[
        "no_kwargs",
        "one_plain_kwarg",
        "one_df_kwarg",
        "one_df_kwarg_and_one_plain_kwarg",
    ],
)
def test__inspect_kwargs(input_and_expected_fn, spark_session):
    """A unit test for inspect_kwargs."""
    pandas_df = pd.DataFrame(
        {"spend": [10, 10, 20, 40, 40, 50], "signups": [1, 10, 50, 100, 200, 400]}
    )
    df = spark_session.createDataFrame(pandas_df)
    input_, expected = input_and_expected_fn(df)
    assert h_spark._inspect_kwargs(input_) == expected


def test__get_pandas_annotations_no_pandas():
    """Unit test for _get_pandas_annotations()."""

    def no_pandas(a: int, b: float) -> float:
        return a * b

    assert h_spark._get_pandas_annotations(node.Node.from_fn(no_pandas), {}) == {
        "a": False,
        "b": False,
    }


def test__get_pandas_annotations_with_pandas():
    def with_pandas(a: pd.Series) -> pd.Series:
        return a * 2

    assert h_spark._get_pandas_annotations(node.Node.from_fn(with_pandas), {}) == {"a": True}


def test__get_pandas_annotations_with_annotated_pandas():
    IntSeries = htypes.column[pd.Series, int]

    def with_pandas(a: IntSeries) -> IntSeries:
        return a * 2

    assert h_spark._get_pandas_annotations(node.Node.from_fn(with_pandas), {}) == {"a": True}


def test__get_pandas_annotations_with_pandas_and_other_default():
    def with_pandas_and_other_default(a: pd.Series, b: int) -> pd.Series:
        return a * b

    assert h_spark._get_pandas_annotations(
        node.Node.from_fn(with_pandas_and_other_default), {"b": 2}
    ) == {"a": True}


def test__get_pandas_annotations_with_pandas_and_other_default_and_one_more():
    def with_pandas_and_other_default_with_one_more(a: pd.Series, c: int, b: int = 2) -> pd.Series:
        return a * b * c

    assert h_spark._get_pandas_annotations(
        node.Node.from_fn(with_pandas_and_other_default_with_one_more), {"b": 2}
    ) == {
        "a": True,
        "c": False,
    }


def test__bind_parameters_to_callable():
    """Unit test for _bind_parameters_to_callable()."""
    actual_kwargs = {"a": 1, "b": 2}
    df_columns = {"b"}
    node_input_types = {
        "a": (int, node.DependencyType.REQUIRED),
        "b": (int, node.DependencyType.REQUIRED),
    }
    df_params, params_to_bind = h_spark._determine_parameters_to_bind(
        actual_kwargs, df_columns, node_input_types, "test"
    )
    assert isinstance(df_params["b"], Column)
    assert params_to_bind == {"a": 1}
    assert str(df_params["b"]) == str(column("b"))  # hacky, but compare string representation.


def test__bind_parameters_to_callable_with_defaults_provided():
    """Unit test for _bind_parameters_to_callable()."""
    actual_kwargs = {"a": 1, "b": 2, "c": 2}
    df_columns = {"b"}
    node_input_types = {
        "a": (int, node.DependencyType.REQUIRED),
        "b": (int, node.DependencyType.REQUIRED),
        "c": (int, node.DependencyType.OPTIONAL),
    }
    df_params, params_to_bind = h_spark._determine_parameters_to_bind(
        actual_kwargs, df_columns, node_input_types, "test"
    )
    assert isinstance(df_params["b"], Column)
    assert params_to_bind == {"a": 1, "c": 2}
    assert str(df_params["b"]) == str(column("b"))  # hacky, but compare string representation.


def test__bind_parameters_to_callable_with_defaults_not_provided():
    """Unit test for _bind_parameters_to_callable()."""
    actual_kwargs = {"a": 1, "b": 2, "c": 2}
    df_columns = {"b"}
    node_input_types = {
        "a": (int, node.DependencyType.REQUIRED),
        "b": (int, node.DependencyType.REQUIRED),
        "c": (int, node.DependencyType.OPTIONAL),
    }
    df_params, params_to_bind = h_spark._determine_parameters_to_bind(
        actual_kwargs, df_columns, node_input_types, "test"
    )
    assert isinstance(df_params["b"], Column)
    assert params_to_bind == {"a": 1, "c": 2}
    assert str(df_params["b"]) == str(column("b"))  # hacky, but compare string representation.


def test__lambda_udf_plain_func(spark_session):
    """Tests plain UDF function"""

    def base_func(a: int, b: int) -> int:
        return a + b

    base_spark_df = spark_session.createDataFrame(pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}))
    node_ = node.Node.from_fn(base_func)
    new_df = h_spark._lambda_udf(base_spark_df, node_, {})
    assert new_df.collect() == [
        Row(a=1, b=4, test=5),
        Row(a=2, b=5, test=7),
        Row(a=3, b=6, test=9),
    ]


def test__lambda_udf_pandas_func(spark_session):
    """Tests pandas UDF function"""

    def base_func(a: pd.Series, b: pd.Series) -> htypes.column[pd.Series, int]:
        return a + b

    base_spark_df = spark_session.createDataFrame(pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}))
    node_ = node.Node.from_fn(base_func)

    new_df = h_spark._lambda_udf(base_spark_df, node_, {})
    assert new_df.collect() == [
        Row(a=1, b=4, test=5),
        Row(a=2, b=5, test=7),
        Row(a=3, b=6, test=9),
    ]


def test__lambda_udf_pandas_func_error(spark_session):
    """Tests it errors on a bad pandas UDF function"""

    def base_func(a: pd.Series, b: int) -> htypes.column[pd.Series, int]:
        return a + b

    base_spark_df = spark_session.createDataFrame(pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}))
    node_ = node.Node.from_fn(base_func)

    with pytest.raises(ValueError):
        h_spark._lambda_udf(base_spark_df, node_, {"a": 1})


def test_smoke_screen_udf_graph_adapter(spark_session):
    """Tests that we can run the PySparkUDFGraphAdapter on a simple graph.

    THe graph has a pandas UDF, a plain UDF that depends on the output of the pandas UDF, and
    also has a parameter bound to it, and then an extra function that isn't satisfied by the
    dataframe, so we add the result as a literal. This should exercise all the code paths
    at least in the result_builder.

    """
    input_df = spark_session.createDataFrame(pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}))
    dr = driver.Driver({}, pyspark_udfs, adapter=h_spark.PySparkUDFGraphAdapter())
    inputs = {"a": input_df, "b": input_df, "c": 4, "d": 5}
    output_df = dr.execute(["base_func", "base_func2", "base_func3"], inputs=inputs)
    assert output_df.collect() == [
        Row(a=1, b=4, base_func=5, base_func2=9, base_func3=9),
        Row(a=2, b=5, base_func=7, base_func2=11, base_func3=9),
        Row(a=3, b=6, base_func=9, base_func2=13, base_func3=9),
    ]


# Test cases for python_to_spark_type function
@pytest.mark.parametrize(
    "python_type,expected_spark_type",
    [
        (int, types.IntegerType()),
        (float, types.FloatType()),
        (bool, types.BooleanType()),
        (str, types.StringType()),
        (bytes, types.BinaryType()),
    ],
)
def test_python_to_spark_type_valid(python_type, expected_spark_type):
    assert h_spark.python_to_spark_type(python_type) == expected_spark_type


@pytest.mark.parametrize("invalid_python_type", [list, dict, tuple, set])
def test_python_to_spark_type_invalid(invalid_python_type):
    with pytest.raises(ValueError, match=f"Unsupported Python type: {invalid_python_type}"):
        h_spark.python_to_spark_type(invalid_python_type)


# Test cases for get_spark_type function
# 1. Basic Python types
@pytest.mark.parametrize(
    "return_type,expected_spark_type",
    [
        (int, types.IntegerType()),
        (float, types.FloatType()),
        (bool, types.BooleanType()),
        (str, types.StringType()),
        (bytes, types.BinaryType()),
    ],
)
def test_get_spark_type_basic_types(return_type, expected_spark_type):
    assert h_spark.get_spark_type(return_type) == expected_spark_type


# 2. Lists of basic Python types
@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python 3.9 or higher")
@pytest.mark.parametrize(
    "return_type,expected_spark_type",
    [
        (int, types.ArrayType(types.IntegerType())),
        (float, types.ArrayType(types.FloatType())),
        (bool, types.ArrayType(types.BooleanType())),
        (str, types.ArrayType(types.StringType())),
        (bytes, types.ArrayType(types.BinaryType())),
    ],
)
def test_get_spark_type_list_types(return_type, expected_spark_type):
    return_type = list[return_type]  # type: ignore
    assert h_spark.get_spark_type(return_type) == expected_spark_type


# 3. Numpy types (assuming you have a numpy_to_spark_type function that handles these)
@pytest.mark.parametrize(
    "return_type,expected_spark_type",
    [
        (np.int64, types.IntegerType()),
        (np.float64, types.FloatType()),
        (np.bool_, types.BooleanType()),
    ],
)
def test_get_spark_type_numpy_types(return_type, expected_spark_type):
    assert h_spark.get_spark_type(return_type) == expected_spark_type


# 4. Unsupported types
@pytest.mark.parametrize(
    "unsupported_return_type",
    [dict, set, tuple],  # Add other unsupported types as needed
)
def test_get_spark_type_unsupported(unsupported_return_type):
    with pytest.raises(
        ValueError,
        match=f"Currently unsupported return type {unsupported_return_type}.",
    ):
        h_spark.get_spark_type(unsupported_return_type)


# Dummy values for the tests
@pytest.fixture
def dummy_kwargs():
    return {}


@pytest.fixture
def dummy_df(spark_session):
    return spark_session.createDataFrame(pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}))


@pytest.fixture
def dummy_udf():
    def dummyfunc(x: int) -> int:
        return x

    return dummyfunc


def test_base_spark_executor_end_to_end(spark_session):
    # TODO -- make this simpler to call, and not require all these constructs
    dr = (
        driver.Builder()
        .with_modules(basic_spark_dag)
        .with_adapter(base.SimplePythonGraphAdapter(base.DictResult()))
        .build()
    )
    # dr.visualize_execution(
    #     ["processed_df_as_pandas"], "./out", {}, inputs={"spark_session": spark_session}
    # )
    df = dr.execute(["processed_df_as_pandas"], inputs={"spark_session": spark_session})[
        "processed_df_as_pandas"
    ]
    expected_data = {
        "a_times_key": [2, 10, 24, 44, 70],
        "b_times_key": [5, 16, 33, 56, 85],
        "a_plus_b_plus_c": [10.5, 20.0, 29.5, 39.0, 48.5],
    }
    expected_df = pd.DataFrame(expected_data)
    pd.testing.assert_frame_equal(df, expected_df, check_names=False, check_dtype=False)


def test_base_spark_executor_end_to_end_with_mode_select(spark_session):
    # TODO -- make this simpler to call, and not require all these constructs
    dr = (
        driver.Builder()
        .with_modules(basic_spark_dag)
        .with_adapter(base.SimplePythonGraphAdapter(base.DictResult()))
        .with_config({"mode": "select"})
        .build()
    )
    # dr.visualize_execution(
    #     ["processed_df_as_pandas"], "./out", {}, inputs={"spark_session": spark_session}
    # )
    df = dr.execute(["processed_df_as_pandas"], inputs={"spark_session": spark_session})[
        "processed_df_as_pandas"
    ]
    expected_data = {
        "a_times_key": [2, 10, 24, 44, 70],
        "a_plus_b_plus_c": [10.5, 20.0, 29.5, 39.0, 48.5],
    }
    expected_df = pd.DataFrame(expected_data)
    pd.testing.assert_frame_equal(df, expected_df, check_names=False, check_dtype=False)


def test_base_spark_executor_end_to_end_with_select_decorator(spark_session):
    # copy of the test above -- they should be the same
    dr = (
        driver.Builder()
        .with_modules(basic_spark_dag)
        .with_adapter(base.SimplePythonGraphAdapter(base.DictResult()))
        .with_config({"mode": "select_decorator"})
        .build()
    )
    # dr.visualize_execution(
    #     ["processed_df_as_pandas"], "./out", {}, inputs={"spark_session": spark_session}
    # )
    df = dr.execute(["processed_df_as_pandas"], inputs={"spark_session": spark_session})[
        "processed_df_as_pandas"
    ]
    expected_data = {
        "a_times_key": [2, 10, 24, 44, 70],
        "a_plus_b_plus_c": [10.5, 20.0, 29.5, 39.0, 48.5],
    }
    expected_df = pd.DataFrame(expected_data)
    pd.testing.assert_frame_equal(df, expected_df, check_names=False, check_dtype=False)


def test_base_spark_executor_end_to_end_external_dependencies(spark_session):
    # TODO -- make this simpler to call, and not require all these constructs
    dr = (
        driver.Builder()
        .with_modules(spark_dag_external_dependencies)
        .with_adapter(base.SimplePythonGraphAdapter(base.DictResult()))
        .build()
    )
    dfs = dr.execute(
        ["processed_df_as_pandas"],
        inputs={"spark_session": spark_session},
    )

    expected_df = pd.DataFrame({"a": [2, 3, 4, 5], "b": [4, 6, 8, 10]})
    processed_df_as_pandas = pd.DataFrame(dfs["processed_df_as_pandas"])
    pd.testing.assert_frame_equal(
        processed_df_as_pandas, expected_df, check_names=False, check_dtype=False
    )


def test_base_spark_executor_end_to_end_multiple_with_columns(spark_session):
    dr = (
        driver.Builder()
        .with_modules(spark_dag_multiple_with_columns)
        .with_adapter(base.SimplePythonGraphAdapter(base.DictResult()))
        .build()
    )
    df = dr.execute(["final"], inputs={"spark_session": spark_session})["final"].sort_index(axis=1)

    expected_df = pd.DataFrame(
        {
            "d_raw": [1, 4, 7, 10],
            "e_raw": [2, 5, 8, 11],
            "f_raw": [5, 10, 15, 20],
            "d": [6, 9, 12, 15],
            "f": [17.5, 35.0, 52.5, 70.0],
            "e": [12.3, 18.299999, 24.299999, 30.299999],
            "multiply_d_e_f_key": [1291.5, 11529.0, 45927.0, 127260.0],
            "key": [1, 2, 3, 4],
            "a_times_key": [2, 10, 24, 44],
            "b_times_key": [5, 16, 33, 56],
            "a_plus_b_plus_c": [10.5, 20.0, 29.5, 39.0],
        }
    ).sort_index(axis=1)
    pd.testing.assert_frame_equal(df, expected_df, check_names=False, check_dtype=False)


def _only_pyspark_dataframe_parameter(foo: DataFrame) -> DataFrame:
    pass


def _no_pyspark_dataframe_parameter(foo: int) -> int:
    pass


def _one_pyspark_dataframe_parameter(foo: DataFrame, bar: int) -> DataFrame:
    pass


def _two_pyspark_dataframe_parameters(foo: DataFrame, bar: int, baz: DataFrame) -> DataFrame:
    pass


@pytest.mark.parametrize(
    "fn,requested_parameter,expected",
    [
        (_only_pyspark_dataframe_parameter, "foo", "foo"),
        (_one_pyspark_dataframe_parameter, "foo", "foo"),
        (_one_pyspark_dataframe_parameter, None, "foo"),
        (_two_pyspark_dataframe_parameters, "foo", "foo"),
        (_two_pyspark_dataframe_parameters, "baz", "baz"),
    ],
)
def test_derive_dataframe_parameter_succeeds(fn, requested_parameter, expected):
    assert h_spark.derive_dataframe_parameter_from_fn(fn, requested_parameter) == expected
    n = node.Node.from_fn(fn)
    assert h_spark.derive_dataframe_parameter_from_node(n, requested_parameter) == expected


@pytest.mark.parametrize(
    "fn,requested_parameter",
    [
        (_no_pyspark_dataframe_parameter, "foo"),
        (_no_pyspark_dataframe_parameter, None),
        (_one_pyspark_dataframe_parameter, "baz"),
        (_two_pyspark_dataframe_parameters, "bar"),
        (_two_pyspark_dataframe_parameters, None),
    ],
)
def test_derive_dataframe_parameter_fails(fn, requested_parameter):
    with pytest.raises(ValueError):
        h_spark.derive_dataframe_parameter_from_fn(fn, requested_parameter)
        n = node.Node.from_fn(fn)
        h_spark.derive_dataframe_parameter_from_node(n, requested_parameter)


def test_prune_nodes_no_select():
    nodes = [
        node.Node.from_fn(fn) for fn in [basic_spark_dag.a, basic_spark_dag.b, basic_spark_dag.c]
    ]
    select = None
    assert {n for n in prune_nodes(nodes, select)} == set(nodes)


def test_prune_nodes_single_select():
    nodes = [
        node.Node.from_fn(fn) for fn in [basic_spark_dag.a, basic_spark_dag.b, basic_spark_dag.c]
    ]
    select = ["a", "b"]
    assert {n for n in prune_nodes(nodes, select)} == set(nodes[0:2])


def test_generate_nodes_invalid_select():
    dec = h_spark.with_columns(
        basic_spark_dag.a,
        basic_spark_dag.b,
        basic_spark_dag.c,
        select=["d"],  # not a node
        columns_to_pass=["a_raw", "b_raw", "c_raw", "key"],
    )
    with pytest.raises(ValueError):

        def df_as_pandas(df: DataFrame) -> pd.DataFrame:
            return df.toPandas()

        dummy_node = node.Node.from_fn(df_as_pandas)
        injectable_params = NodeInjector.find_injectable_params([dummy_node])

        dec.inject_nodes(params=injectable_params, config={}, fn=df_as_pandas)


def test_with_columns_generate_nodes_no_select():
    dec = h_spark.with_columns(
        basic_spark_dag.a,
        basic_spark_dag.b,
        basic_spark_dag.c,
        columns_to_pass=["a_raw", "b_raw", "c_raw", "key"],
    )

    def df_as_pandas(df: DataFrame) -> pd.DataFrame:
        return df.toPandas()

    dummy_node = node.Node.from_fn(df_as_pandas)
    injectable_params = NodeInjector.find_injectable_params([dummy_node])

    nodes, _ = dec.inject_nodes(params=injectable_params, config={}, fn=df_as_pandas)

    nodes_by_names = {n.name: n for n in nodes}
    assert set(nodes_by_names.keys()) == {
        "df_as_pandas.a",
        "df_as_pandas.b",
        "df_as_pandas.c",
    }


def test_with_columns_generate_nodes_select():
    dec = h_spark.with_columns(
        basic_spark_dag.a,
        basic_spark_dag.b,
        basic_spark_dag.c,
        columns_to_pass=["a_raw", "b_raw", "c_raw", "key"],
        select=["c"],
    )

    def df_as_pandas(df: DataFrame) -> pd.DataFrame:
        return df.toPandas()

    dummy_node = node.Node.from_fn(df_as_pandas)
    injectable_params = NodeInjector.find_injectable_params([dummy_node])

    nodes, _ = dec.inject_nodes(params=injectable_params, config={}, fn=df_as_pandas)
    nodes_by_names = {n.name: n for n in nodes}
    assert set(nodes_by_names.keys()) == {
        "df_as_pandas.c",
    }


def test_with_columns_generate_nodes_select_append_mode():
    dec = h_spark.with_columns(
        a_dag,
        columns_to_pass=["input"],
        select=["c"],
    )

    def df_as_pandas(df: DataFrame) -> pd.DataFrame:
        return df.toPandas()

    dummy_node = node.Node.from_fn(df_as_pandas)
    injectable_params = NodeInjector.find_injectable_params([dummy_node])

    nodes, _ = dec.inject_nodes(params=injectable_params, config={}, fn=df_as_pandas)

    nodes_by_names = {n.name: n for n in nodes}
    assert set(nodes_by_names.keys()) == {
        "df_as_pandas._select",
        "df_as_pandas.a",
        "df_as_pandas.b",
        "df_as_pandas.c",
    }


def test_with_columns_generate_nodes_select_mode_select():
    dec = h_spark.with_columns(
        basic_spark_dag.a,
        basic_spark_dag.b,
        basic_spark_dag.c,
        columns_to_pass=["a_raw", "b_raw", "c_raw", "key"],
        select=["c"],
        mode="select",
    )

    def df_as_pandas(df: DataFrame) -> pd.DataFrame:
        return df.toPandas()

    dummy_node = node.Node.from_fn(df_as_pandas)
    injectable_params = NodeInjector.find_injectable_params([dummy_node])

    nodes, _ = dec.inject_nodes(params=injectable_params, config={}, fn=df_as_pandas)
    nodes_by_names = {n.name: n for n in nodes}
    assert set(nodes_by_names.keys()) == {
        "df_as_pandas.c",
        "df_as_pandas._select",
    }


def test_with_columns_generate_nodes_specify_namespace():
    dec = h_spark.with_columns(
        basic_spark_dag.a,
        basic_spark_dag.b,
        basic_spark_dag.c,
        columns_to_pass=["a_raw", "b_raw", "c_raw", "key"],
        namespace="foo",
    )

    def df_as_pandas(df: DataFrame) -> pd.DataFrame:
        return df.toPandas()

    dummy_node = node.Node.from_fn(df_as_pandas)
    injectable_params = NodeInjector.find_injectable_params([dummy_node])

    nodes, _ = dec.inject_nodes(params=injectable_params, config={}, fn=df_as_pandas)
    nodes_by_names = {n.name: n for n in nodes}
    assert set(nodes_by_names.keys()) == {
        "foo.a",
        "foo.b",
        "foo.c",
    }


def test__format_pandas_udf():
    assert (
        h_spark._format_pandas_udf("foo", ["a", "b"]).strip()
        == "def foo(a: pd.Series, b: pd.Series) -> pd.Series:\n"
        "    return partial_fn(a=a, b=b)"
    )


def test__format_standard_udf():
    assert (
        h_spark._format_udf("foo", ["b", "a"]).strip() == "def foo(b, a):\n"
        "    return partial_fn(b=b, a=a)"
    )


def test_sparkify_node():
    def foo(
        a_from_upstream: pd.Series,
        b_from_upstream: pd.Series,
        c_from_df: pd.Series,
        d_fixed: int,
    ) -> htypes.column[pd.Series, int]:
        return a_from_upstream + b_from_upstream + c_from_df + d_fixed

    node_ = node.Node.from_fn(foo)
    sparkified = h_spark.sparkify_node_with_udf(
        node_,
        "df_upstream",
        "df_base",
        None,
        {"a_from_upstream", "b_from_upstream"},
        {"c_from_df"},
    )
    # Superset of all the original nodes except the ones from the dataframe
    # (as we already have that) both the physical and the logical dependencies
    assert set(sparkified.input_types) == {
        "a_from_upstream",
        "b_from_upstream",
        "d_fixed",
        "df_base",
        "df_upstream",
    }


def test_pyspark_mixed_pandas_udfs_end_to_end():
    # TODO -- make this simpler to call, and not require all these constructs
    dr = (
        driver.Builder()
        .with_modules(spark_dag_mixed_pyspark_pandas_udfs)
        .with_adapter(base.SimplePythonGraphAdapter(base.DictResult()))
        .build()
    )
    # dr.visualize_execution(
    #     ["processed_df_as_pandas_dataframe_with_injected_dataframe"],
    #     "./out",
    #     {},
    #     inputs={"spark_session": spark_session},
    # )
    results = dr.execute(
        [
            "processed_df_as_pandas_dataframe_with_injected_dataframe",
            "processed_df_as_pandas",
        ],
        inputs={"spark_session": spark_session},
    )
    processed_df_as_pandas = results["processed_df_as_pandas"]
    processed_df_as_pandas_dataframe_with_injected_dataframe = results[
        "processed_df_as_pandas_dataframe_with_injected_dataframe"
    ]
    expected_data = {
        "a_times_key": [2, 10, 24, 44, 70],
        "b_times_key": [5, 16, 33, 56, 85],
        "a_plus_b_plus_c": [10.5, 20.0, 29.5, 39.0, 48.5],
    }
    expected_df = pd.DataFrame(expected_data)
    pd.testing.assert_frame_equal(
        processed_df_as_pandas, expected_df, check_names=False, check_dtype=False
    )
    pd.testing.assert_frame_equal(
        processed_df_as_pandas_dataframe_with_injected_dataframe,
        expected_df,
        check_names=False,
        check_dtype=False,
    )


def test_just_pyspark_udfs_end_to_end():
    # TODO -- make this simpler to call, and not require all these constructs
    dr = (
        driver.Builder()
        .with_modules(spark_dag_pyspark_udfs)
        .with_adapter(base.SimplePythonGraphAdapter(base.DictResult()))
        .build()
    )
    # dr.visualize_execution(
    #     ["processed_df_as_pandas_with_injected_dataframe", "processed_df_as_pandas"],
    #     "./out",
    #     {},
    # )
    results = dr.execute(
        ["processed_df_as_pandas_with_injected_dataframe", "processed_df_as_pandas"]
    )
    processed_df_as_pandas_with_injected_dataframe = results[
        "processed_df_as_pandas_with_injected_dataframe"
    ]
    processed_df_as_pandas = results["processed_df_as_pandas"]
    expected_data = {
        "a_times_key": [2, 10, 24, 44, 70],
        "b_times_key": [5, 16, 33, 56, 85],
        "a_plus_b_plus_c": [10.5, 20.0, 29.5, 39.0, 48.5],
    }
    expected_df = pd.DataFrame(expected_data)
    pd.testing.assert_frame_equal(
        processed_df_as_pandas, expected_df, check_names=False, check_dtype=False
    )
    pd.testing.assert_frame_equal(
        processed_df_as_pandas_with_injected_dataframe,
        expected_df,
        check_names=False,
        check_dtype=False,
    )


# is default
def pyspark_fn_1(foo: DataFrame) -> DataFrame:
    pass


# is default
def pyspark_fn_2(foo: DataFrame, bar: int) -> DataFrame:
    pass


def not_pyspark_fn(foo: DataFrame, bar: DataFrame) -> DataFrame:
    pass


@pytest.mark.parametrize(
    "fn,expected", [(pyspark_fn_1, True), (pyspark_fn_2, True), (not_pyspark_fn, False)]
)
def test_is_default_pyspark_node(fn, expected):
    node_ = node.Node.from_fn(fn)
    assert h_spark.require_columns.is_default_pyspark_udf(node_) == expected


def fn_test_initial_schema_1(a: int, b: int) -> int:
    return a + b


def fn_test_initial_schema_2(fn_test_initial_schema_1: int, c: int = 1) -> int:
    return fn_test_initial_schema_1 + c


def test_create_selector_node(spark_session):
    selector_node = h_spark.with_columns.create_selector_node("foo", ["a", "b"], "select")
    assert selector_node.name == "select"
    pandas_df = pd.DataFrame(
        {
            "a": [10, 10, 20, 40, 40, 50],
            "b": [1, 10, 50, 100, 200, 400],
            "c": [1, 2, 3, 4, 5, 6],
        }
    )
    df = spark_session.createDataFrame(pandas_df)
    transformed = selector_node(foo=df).toPandas()
    pd.testing.assert_frame_equal(
        transformed, pandas_df[["a", "b"]], check_names=False, check_dtype=False
    )


def test_spark_input_adapter_dataframe(spark_session):
    # We have to do these at is is very difficult to mock out connect.x objects
    df = spark_session.range(1)
    assert SparkInputValidator().do_validate_input(node_type=DataFrame, input_value=df)


def test_spark_input_adapter_connector():
    # We have to do these at is is very difficult to mock out connect.x objects
    class ConnectSparkSession(CSparkSession):
        def __init__(self):
            pass

    assert SparkInputValidator().do_validate_input(
        node_type=SparkSession, input_value=ConnectSparkSession()
    )
