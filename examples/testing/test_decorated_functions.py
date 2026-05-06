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

"""Testing functions that use Hamilton decorators.

There are two complementary techniques here:

1. **Test the underlying callable.** Decorators such as ``@tag``,
   ``@parameterize`` and ``@extract_columns`` do not change what the function
   *does* when you call it directly -- they change how Hamilton wires it into
   the DAG. A direct call is the cheapest unit test.

2. **Test the expanded DAG.** Build a Driver, run it, and assert on the
   generated nodes (e.g. ``spend_in_thousands``, ``scaled_spend``). This is the
   only way to verify that the decorator wiring is correct.
"""

import decorated_functions
import pandas as pd

from hamilton import driver


def test_decorated_function_is_callable_directly() -> None:
    """`@parameterize` does not stop the function from being called directly."""
    result = decorated_functions.scaled(raw_value=pd.Series([1000.0, 2000.0]), divisor=1000.0)

    pd.testing.assert_series_equal(result, pd.Series([1.0, 2.0]))


def test_total_signups_ignores_tag() -> None:
    """`@tag` is metadata only -- the function still computes a sum."""
    result = decorated_functions.total_signups(signups=pd.Series([1, 2, 3]))

    assert result == 6


def test_parameterize_expands_into_two_nodes() -> None:
    """Build a Driver to verify `@parameterize` produced both nodes correctly."""
    dr = driver.Builder().with_modules(decorated_functions).build()

    inputs = {
        "spend": pd.Series([1000.0, 2000.0, 3000.0]),
        "signups": pd.Series([100.0, 200.0, 300.0]),
    }

    result = dr.execute(["spend_in_thousands", "signups_in_hundreds"], inputs=inputs)

    pd.testing.assert_series_equal(
        result["spend_in_thousands"], pd.Series([1.0, 2.0, 3.0]), check_names=False
    )
    pd.testing.assert_series_equal(
        result["signups_in_hundreds"], pd.Series([1.0, 2.0, 3.0]), check_names=False
    )


def test_extract_columns_exposes_each_column_as_a_node() -> None:
    """`@extract_columns` should make `scaled_spend` and `scaled_signups` queryable."""
    dr = driver.Builder().with_modules(decorated_functions).build()

    inputs = {
        "spend": pd.Series([1000.0, 2000.0]),
        "signups": pd.Series([100.0, 200.0]),
    }

    result = dr.execute(["scaled_spend", "scaled_signups"], inputs=inputs)

    pd.testing.assert_series_equal(result["scaled_spend"], pd.Series([1.0, 2.0]), check_names=False)
    pd.testing.assert_series_equal(
        result["scaled_signups"], pd.Series([1.0, 2.0]), check_names=False
    )
