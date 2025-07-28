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
import pytest

from hamilton import driver, node
from hamilton.function_modifiers.base import NodeInjector
from hamilton.plugins.h_pandas import with_columns

from .resources import with_columns_end_to_end


def test__create_column_nodes():
    def dummy_fn_with_columns(col_1: pd.Series) -> pd.Series:
        return col_1 + 100

    def dummy_df() -> pd.DataFrame:
        return pd.DataFrame({"col_1": [1, 2, 3, 4], "col_2": [11, 12, 13, 14]})

    def target_fn(upstream_df: pd.DataFrame) -> pd.DataFrame:
        return upstream_df

    decorator = with_columns(
        dummy_fn_with_columns, columns_to_pass=["col_1", "col_2"], select=["dummy_fn_with_columns"]
    )

    column_nodes = decorator._create_column_nodes(
        fn=target_fn, inject_parameter="upstream_df", params={"upstream_df": pd.DataFrame}
    )

    col1 = column_nodes[0]
    col2 = column_nodes[1]

    assert col1.name == "col_1"
    assert col2.name == "col_2"

    pd.testing.assert_series_equal(
        col1.callable(upstream_df=dummy_df()),
        pd.Series([1, 2, 3, 4]),
        check_names=False,
    )

    pd.testing.assert_series_equal(
        col2.callable(upstream_df=dummy_df()),
        pd.Series([11, 12, 13, 14]),
        check_names=False,
    )


def test__get_initial_nodes_when_extracting_columns():
    def dummy_fn_with_columns(col_1: pd.Series) -> pd.Series:
        return col_1 + 100

    def dummy_df() -> pd.DataFrame:
        return pd.DataFrame({"col_1": [1, 2, 3, 4], "col_2": [11, 12, 13, 14]})

    def target_fn(upstream_df: pd.DataFrame) -> pd.DataFrame:
        return upstream_df

    dummy_node = node.Node.from_fn(target_fn)

    decorator = with_columns(
        dummy_fn_with_columns, columns_to_pass=["col_1", "col_2"], select=["dummy_fn_with_columns"]
    )
    injectable_params = NodeInjector.find_injectable_params([dummy_node])

    inject_parameter, initial_nodes = decorator.get_initial_nodes(
        fn=target_fn, params=injectable_params
    )

    assert inject_parameter == "upstream_df"
    assert len(initial_nodes) == 2


def test__get_initial_nodes_when_passing_dataframe():
    def dummy_fn_with_columns(col_1: pd.Series) -> pd.Series:
        return col_1 + 100

    def dummy_df() -> pd.DataFrame:
        return pd.DataFrame({"col_1": [1, 2, 3, 4], "col_2": [11, 12, 13, 14]})

    def target_fn(upstream_df: pd.DataFrame) -> pd.DataFrame:
        return upstream_df

    dummy_node = node.Node.from_fn(target_fn)

    decorator = with_columns(
        dummy_fn_with_columns, on_input="upstream_df", select=["dummy_fn_with_columns"]
    )
    injectable_params = NodeInjector.find_injectable_params([dummy_node])
    inject_parameter, initial_nodes = decorator.get_initial_nodes(
        fn=target_fn, params=injectable_params
    )

    assert inject_parameter == "upstream_df"
    assert len(initial_nodes) == 0


def test_first_parameter_is_dataframe():
    def dummy_fn_with_columns(col_1: pd.Series) -> pd.Series:
        return col_1 + 100

    def target_fn(upstream_df: int) -> pd.DataFrame:
        return upstream_df

    dummy_node = node.Node.from_fn(target_fn)

    decorator = with_columns(
        dummy_fn_with_columns, columns_to_pass=["col_1"], select=["dummy_fn_with_columns"]
    )
    injectable_params = NodeInjector.find_injectable_params([dummy_node])

    # Raises error that is not pandas dataframe
    with pytest.raises(NotImplementedError):
        decorator.get_initial_nodes(fn=target_fn, params=injectable_params)


def test_create_column_nodes_pass_dataframe():
    def dummy_fn_with_columns(col_1: pd.Series) -> pd.Series:
        return col_1 + 100

    def target_fn(some_var: int, upstream_df: pd.DataFrame) -> pd.DataFrame:
        return upstream_df

    dummy_node = node.Node.from_fn(target_fn)

    decorator = with_columns(
        dummy_fn_with_columns, on_input="upstream_df", select=["dummy_fn_with_columns"]
    )
    injectable_params = NodeInjector.find_injectable_params([dummy_node])
    inject_parameter, initial_nodes = decorator.get_initial_nodes(
        fn=target_fn, params=injectable_params
    )

    assert inject_parameter == "upstream_df"
    assert len(initial_nodes) == 0


def test_create_column_nodes_extract_single_columns():
    def dummy_fn_with_columns(col_1: pd.Series) -> pd.Series:
        return col_1 + 100

    def dummy_df() -> pd.DataFrame:
        return pd.DataFrame({"col_1": [1, 2, 3, 4], "col_2": [11, 12, 13, 14]})

    def target_fn(upstream_df: pd.DataFrame) -> pd.DataFrame:
        return upstream_df

    dummy_node = node.Node.from_fn(target_fn)

    decorator = with_columns(
        dummy_fn_with_columns, columns_to_pass=["col_1"], select=["dummy_fn_with_columns"]
    )
    injectable_params = NodeInjector.find_injectable_params([dummy_node])
    inject_parameter, initial_nodes = decorator.get_initial_nodes(
        fn=target_fn, params=injectable_params
    )

    assert inject_parameter == "upstream_df"
    assert len(initial_nodes) == 1
    assert initial_nodes[0].name == "col_1"
    assert initial_nodes[0].type == pd.Series
    pd.testing.assert_series_equal(
        initial_nodes[0].callable(upstream_df=dummy_df()),
        pd.Series([1, 2, 3, 4]),
        check_names=False,
    )


def test_create_column_nodes_extract_multiple_columns():
    def dummy_fn_with_columns(col_1: pd.Series) -> pd.Series:
        return col_1 + 100

    def dummy_df() -> pd.DataFrame:
        return pd.DataFrame({"col_1": [1, 2, 3, 4], "col_2": [11, 12, 13, 14]})

    def target_fn(upstream_df: pd.DataFrame) -> pd.DataFrame:
        return upstream_df

    dummy_node = node.Node.from_fn(target_fn)

    decorator = with_columns(
        dummy_fn_with_columns, columns_to_pass=["col_1", "col_2"], select=["dummy_fn_with_columns"]
    )
    injectable_params = NodeInjector.find_injectable_params([dummy_node])

    inject_parameter, initial_nodes = decorator.get_initial_nodes(
        fn=target_fn, params=injectable_params
    )

    assert inject_parameter == "upstream_df"
    assert len(initial_nodes) == 2
    assert initial_nodes[0].name == "col_1"
    assert initial_nodes[1].name == "col_2"
    assert initial_nodes[0].type == pd.Series
    assert initial_nodes[1].type == pd.Series
    pd.testing.assert_series_equal(
        initial_nodes[0].callable(upstream_df=dummy_df()),
        pd.Series([1, 2, 3, 4]),
        check_names=False,
    )
    pd.testing.assert_series_equal(
        initial_nodes[1].callable(upstream_df=dummy_df()),
        pd.Series([11, 12, 13, 14]),
        check_names=False,
    )


def test_no_matching_select_column_error():
    def dummy_fn_with_columns(col_1: pd.Series) -> pd.Series:
        return col_1 + 100

    def target_fn(upstream_df: pd.DataFrame) -> pd.DataFrame:
        return upstream_df

    dummy_node = node.Node.from_fn(target_fn)
    select = "wrong_column"

    decorator = with_columns(
        dummy_fn_with_columns, columns_to_pass=["col_1", "col_2"], select=select
    )
    injectable_params = NodeInjector.find_injectable_params([dummy_node])

    with pytest.raises(ValueError):
        decorator.inject_nodes(injectable_params, {}, fn=target_fn)


def test_append_into_original_df():
    def dummy_fn_with_columns(col_1: pd.Series) -> pd.Series:
        return col_1 + 100

    def dummy_df() -> pd.DataFrame:
        return pd.DataFrame({"col_1": [1, 2, 3, 4], "col_2": [11, 12, 13, 14]})

    def target_fn(upstream_df: pd.DataFrame) -> pd.DataFrame:
        return upstream_df

    decorator = with_columns(
        dummy_fn_with_columns, columns_to_pass=["col_1", "col_2"], select=["dummy_fn_with_columns"]
    )

    output_nodes, _ = decorator.chain_subdag_nodes(
        fn=target_fn, inject_parameter="upstream_df", generated_nodes=[]
    )
    merge_node = output_nodes[-1]

    output_df = merge_node.callable(
        upstream_df=dummy_df(),
        dummy_fn_with_columns=dummy_fn_with_columns(col_1=pd.Series([1, 2, 3, 4])),
    )
    assert merge_node.name == "_append"
    assert merge_node.type == pd.DataFrame

    pd.testing.assert_series_equal(output_df["col_1"], pd.Series([1, 2, 3, 4]), check_names=False)
    pd.testing.assert_series_equal(
        output_df["col_2"], pd.Series([11, 12, 13, 14]), check_names=False
    )
    pd.testing.assert_series_equal(
        output_df["dummy_fn_with_columns"], pd.Series([101, 102, 103, 104]), check_names=False
    )


def test_override_original_column_in_df():
    def dummy_df() -> pd.DataFrame:
        return pd.DataFrame({"col_1": [1, 2, 3, 4], "col_2": [11, 12, 13, 14]})

    def target_fn(upstream_df: pd.DataFrame) -> pd.DataFrame:
        return upstream_df

    def col_1() -> pd.Series:
        return pd.Series([0, 3, 5, 7])

    decorator = with_columns(col_1, on_input="upstream_df", select=["col_1"])
    output_nodes, _ = decorator.chain_subdag_nodes(
        fn=target_fn, inject_parameter="upstream_df", generated_nodes=[]
    )
    merge_node = output_nodes[-1]

    output_df = merge_node.callable(upstream_df=dummy_df(), col_1=col_1())
    assert merge_node.name == "_append"
    assert merge_node.type == pd.DataFrame

    pd.testing.assert_series_equal(output_df["col_1"], pd.Series([0, 3, 5, 7]), check_names=False)
    pd.testing.assert_series_equal(
        output_df["col_2"], pd.Series([11, 12, 13, 14]), check_names=False
    )


def test_assign_custom_namespace_with_columns():
    def dummy_fn_with_columns(col_1: pd.Series) -> pd.Series:
        return col_1 + 100

    def target_fn(upstream_df: pd.DataFrame) -> pd.DataFrame:
        return upstream_df

    dummy_node = node.Node.from_fn(target_fn)
    decorator = with_columns(
        dummy_fn_with_columns,
        columns_to_pass=["col_1", "col_2"],
        select=["dummy_fn_with_columns"],
        namespace="dummy_namespace",
    )
    nodes_ = decorator.transform_dag([dummy_node], {}, target_fn)
    print(nodes_)
    assert nodes_[0].name == "target_fn"
    assert nodes_[1].name == "dummy_namespace.dummy_fn_with_columns"
    assert nodes_[2].name == "dummy_namespace.col_1"
    assert nodes_[3].name == "dummy_namespace._append"


def test_end_to_end_with_columns_automatic_extract():
    config_5 = {
        "factor": 5,
    }
    dr = driver.Builder().with_modules(with_columns_end_to_end).with_config(config_5).build()
    result = dr.execute(final_vars=["final_df"], inputs={"user_factor": 1000})["final_df"]

    expected_df = pd.DataFrame(
        {
            "col_1": [1, 2, 3, 4],
            "col_2": [11, 12, 13, 14],
            "col_3": [1, 1, 1, 1],
            "subtract_1_from_2": [10, 10, 10, 10],
            "multiply_3": [5, 5, 5, 5],
            "add_1_by_user_adjustment_factor": [1001, 1002, 1003, 1004],
            "multiply_2_by_upstream_3": [33, 36, 39, 42],
        }
    )
    pd.testing.assert_frame_equal(result, expected_df)

    config_7 = {
        "factor": 7,
    }
    dr = driver.Builder().with_modules(with_columns_end_to_end).with_config(config_7).build()
    result = dr.execute(final_vars=["final_df"], inputs={"user_factor": 1000})["final_df"]

    expected_df = pd.DataFrame(
        {
            "col_1": [1, 2, 3, 4],
            "col_2": [11, 12, 13, 14],
            "col_3": [1, 1, 1, 1],
            "subtract_1_from_2": [10, 10, 10, 10],
            "multiply_3": [7, 7, 7, 7],
            "add_1_by_user_adjustment_factor": [1001, 1002, 1003, 1004],
            "multiply_2_by_upstream_3": [33, 36, 39, 42],
        }
    )
    pd.testing.assert_frame_equal(result, expected_df)


def test_end_to_end_with_columns_pass_dataframe():
    config_5 = {
        "factor": 5,
    }
    dr = driver.Builder().with_modules(with_columns_end_to_end).with_config(config_5).build()

    result = dr.execute(final_vars=["final_df_2"])["final_df_2"]
    expected_df = pd.DataFrame(
        {
            "col_1": [1, 2, 3, 4],
            "col_2": [11, 12, 13, 14],
            "col_3": [0, 2, 4, 6],
            "multiply_3": [0, 10, 20, 30],
        }
    )
    pd.testing.assert_frame_equal(result, expected_df)
