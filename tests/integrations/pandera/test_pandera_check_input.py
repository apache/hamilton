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

"""A function with postponed annotations behind Pandera's ``check_input`` becomes a node.

``check_input`` returns a ``functools.wraps`` wrapper that ``pandera.decorators`` defines. The
decorated function's annotations are strings that name the user module's own aliases, so they
resolve only against the user module's namespace.
"""

import pytest

pandera = pytest.importorskip("pandera")

from hamilton import base, driver  # noqa: E402
from hamilton.node import DependencyType, Node  # noqa: E402


def test_check_input_on_polars_lazyframe_with_future_annotations():
    pytest.importorskip("polars")
    from pandera.typing.polars import LazyFrame

    from tests.resources import pandera_check_input_polars as user_module

    fn = user_module.doubled_prices
    assert fn.__globals__["__name__"] == "pandera.decorators", "expected Pandera's wrapper"
    expected_type = LazyFrame[user_module.PriceSchema]

    node_ = Node.from_fn(fn)

    assert node_.type == expected_type
    assert node_.input_types == {"raw_prices": (expected_type, DependencyType.REQUIRED)}

    dr = driver.Builder().with_modules(user_module).with_adapters(base.DictResult()).build()
    result = dr.execute(["doubled_prices"], inputs={"column_name": "price"})
    assert result["doubled_prices"].collect().to_dict(as_series=False) == {"price": [2.0, 5.0]}

    # the node still runs behind Pandera's check: a frame that breaks the schema is refused
    with pytest.raises(pandera.errors.SchemaError):
        dr.execute(["doubled_prices"], inputs={"column_name": "cost"})


def test_check_input_on_pandas_dataframe_with_future_annotations():
    from pandera.typing import DataFrame

    from tests.resources import pandera_check_input_pandas as user_module

    fn = user_module.doubled_prices
    assert fn.__globals__["__name__"] == "pandera.decorators", "expected Pandera's wrapper"
    expected_type = DataFrame[user_module.PriceSchema]

    node_ = Node.from_fn(fn)

    assert node_.type == expected_type
    assert node_.input_types == {"raw_prices": (expected_type, DependencyType.REQUIRED)}

    dr = driver.Builder().with_modules(user_module).with_adapters(base.DictResult()).build()
    result = dr.execute(["doubled_prices"], inputs={"column_name": "price"})
    assert result["doubled_prices"]["price"].tolist() == [2.0, 5.0]

    # the node still runs behind Pandera's check: a frame that breaks the schema is refused
    with pytest.raises(pandera.errors.SchemaError):
        dr.execute(["doubled_prices"], inputs={"column_name": "cost"})
