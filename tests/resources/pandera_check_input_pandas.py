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

"""A node with postponed annotations behind Pandera's ``check_input``, on a pandas DataFrame.

``PADataFrame`` is this module's alias for Pandera's typed DataFrame. ``check_input`` wraps the
function in a wrapper that ``pandera.decorators`` defines, where the alias does not exist.
"""

from __future__ import annotations

import pandas as pd
import pandera.pandas as pa
from pandera.typing import DataFrame as PADataFrame  # noqa: TC002 -- used at runtime


class PriceSchema(pa.DataFrameModel):
    price: float


def raw_prices(column_name: str) -> PADataFrame[PriceSchema]:
    """Not validated here: a ``column_name`` other than ``price`` breaks the schema downstream."""
    return pd.DataFrame({column_name: [1.0, 2.5]})


@pa.check_input(PriceSchema.to_schema())
def doubled_prices(raw_prices: PADataFrame[PriceSchema]) -> PADataFrame[PriceSchema]:
    return raw_prices.assign(price=raw_prices["price"] * 2)
