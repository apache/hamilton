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

import numpy as np
import vaex

from hamilton import base, driver
from hamilton.plugins import h_vaex, vaex_extensions  # noqa F401

from .resources import functions


def test_vaex_column_from_expression():
    adapter = base.SimplePythonGraphAdapter(result_builder=h_vaex.VaexDataFrameResult())
    dr = driver.Driver({}, functions, adapter=adapter)
    result_df = dr.execute(["a", "b", "a_plus_b_expression"])
    assert isinstance(result_df, vaex.dataframe.DataFrame)
    np.testing.assert_allclose(result_df["a_plus_b_expression"].to_numpy(), [3, 5, 7])


def test_vaex_column_from_nparray():
    adapter = base.SimplePythonGraphAdapter(result_builder=h_vaex.VaexDataFrameResult())
    dr = driver.Driver({}, functions, adapter=adapter)
    result_df = dr.execute(["a", "b", "a_plus_b_nparray"])
    assert isinstance(result_df, vaex.dataframe.DataFrame)
    np.testing.assert_allclose(result_df["a_plus_b_nparray"].to_numpy(), [3, 5, 7])


def test_vaex_scalar_among_columns():
    adapter = base.SimplePythonGraphAdapter(result_builder=h_vaex.VaexDataFrameResult())
    dr = driver.Driver({}, functions, adapter=adapter)
    result_df = dr.execute(["a", "b", "a_mean"])
    assert isinstance(result_df, vaex.dataframe.DataFrame)
    np.testing.assert_allclose(result_df["a_mean"].to_numpy(), [2, 2, 2])


def test_vaex_only_scalars():
    adapter = base.SimplePythonGraphAdapter(result_builder=h_vaex.VaexDataFrameResult())
    dr = driver.Driver({}, functions, adapter=adapter)
    result_df = dr.execute(["a_mean", "b_mean"])
    assert isinstance(result_df, vaex.dataframe.DataFrame)
    np.testing.assert_allclose(result_df["a_mean"].to_numpy(), [2])
    np.testing.assert_allclose(result_df["b_mean"].to_numpy(), [3])


def test_vaex_df_among_columns():
    adapter = base.SimplePythonGraphAdapter(result_builder=h_vaex.VaexDataFrameResult())
    dr = driver.Driver({}, functions, adapter=adapter)
    result_df = dr.execute(["a", "b", "ab_as_df"])
    assert isinstance(result_df, vaex.dataframe.DataFrame)
    np.testing.assert_allclose(result_df["a_in_df"].to_numpy(), result_df["a"].to_numpy())
    np.testing.assert_allclose(result_df["b_in_df"].to_numpy(), result_df["b"].to_numpy())
