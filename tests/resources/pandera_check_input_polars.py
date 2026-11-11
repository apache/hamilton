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

"""A node with postponed annotations behind Pandera's ``check_input``, on a Polars LazyFrame.

``PALazyFrame`` is this module's alias for Pandera's typed LazyFrame. ``check_input`` wraps the
function in a wrapper that ``pandera.decorators`` defines, where the alias does not exist.
"""

from __future__ import annotations

import pandera.polars as pa
import polars as pl
from pandera.typing.polars import LazyFrame as PALazyFrame  # noqa: TC002 -- used at runtime


class PriceSchema(pa.DataFrameModel):
    price: float


def raw_prices(column_name: str) -> PALazyFrame[PriceSchema]:
    """Not validated here: a ``column_name`` other than ``price`` breaks the schema downstream."""
    return pl.LazyFrame({column_name: [1.0, 2.5]})


@pa.check_input(PriceSchema.to_schema())
def doubled_prices(raw_prices: PALazyFrame[PriceSchema]) -> PALazyFrame[PriceSchema]:
    return raw_prices.with_columns(pl.col("price") * 2)
