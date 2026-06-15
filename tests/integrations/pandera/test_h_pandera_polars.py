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

import pytest

polars = pytest.importorskip("polars")
pandera = pytest.importorskip("pandera")

import pandera.typing.polars as pa_tp  # noqa: E402
from pandera.api.polars.model import DataFrameModel  # noqa: E402

from hamilton import ad_hoc_utils, driver, node  # noqa: E402
from hamilton.data_quality.base import DataValidationError  # noqa: E402
from hamilton.htypes import get_type_as_string  # noqa: E402
from hamilton.plugins import h_pandera  # noqa: E402


class OHLCVSchema(DataFrameModel):
    open: float
    high: float
    low: float
    close: float
    volume: int


# ---------------------------------------------------------------------------
# D1: get_type_as_string
# ---------------------------------------------------------------------------


def test_get_type_as_string_pandera_polars_lazyframe():
    result = get_type_as_string(pa_tp.LazyFrame[OHLCVSchema])
    assert "LazyFrame" in result
    assert "OHLCVSchema" in result


def test_get_type_as_string_plain_polars_lazyframe():
    """Bare LazyFrame (no type arg) must still return 'LazyFrame' unchanged."""
    import polars as pl

    result = get_type_as_string(pl.LazyFrame)
    assert result == "LazyFrame"


# ---------------------------------------------------------------------------
# D2 / AC-2.1 / AC-2.2: h_pandera.check_output — validator construction
# ---------------------------------------------------------------------------


def test_h_pandera_check_output_polars_lazyframe_builds_validators():
    def my_lazyframe() -> pa_tp.LazyFrame[OHLCVSchema]:
        return polars.LazyFrame(
            {"open": [1.0], "high": [2.0], "low": [0.5], "close": [1.5], "volume": [100]}
        )

    n = node.Node.from_fn(my_lazyframe)
    validators = h_pandera.check_output().get_validators(n)
    assert len(validators) >= 1


def test_h_pandera_check_output_polars_dataframe_builds_validators():
    def my_dataframe() -> pa_tp.DataFrame[OHLCVSchema]:
        return polars.DataFrame(
            {"open": [1.0], "high": [2.0], "low": [0.5], "close": [1.5], "volume": [100]}
        )

    n = node.Node.from_fn(my_dataframe)
    validators = h_pandera.check_output().get_validators(n)
    assert len(validators) >= 1


# ---------------------------------------------------------------------------
# D3: end-to-end via dr.execute
# ---------------------------------------------------------------------------


@h_pandera.check_output()
def valid_ohlcv_lazyframe() -> pa_tp.LazyFrame[OHLCVSchema]:
    return polars.LazyFrame(
        {"open": [1.0], "high": [2.0], "low": [0.5], "close": [1.5], "volume": [100]}
    )


@h_pandera.check_output(importance="fail")
def invalid_ohlcv_lazyframe() -> pa_tp.LazyFrame[OHLCVSchema]:
    # Missing 'volume' column — schema validation should fire
    return polars.LazyFrame({"open": [1.0], "high": [2.0], "low": [0.5], "close": [1.5]})


def test_h_pandera_check_output_polars_lazyframe_passes():
    mod = ad_hoc_utils.create_temporary_module(valid_ohlcv_lazyframe)
    dr = driver.Builder().with_modules(mod).build()
    result = dr.execute(["valid_ohlcv_lazyframe"])
    assert result["valid_ohlcv_lazyframe"] is not None


def test_h_pandera_check_output_polars_lazyframe_fails():
    mod = ad_hoc_utils.create_temporary_module(invalid_ohlcv_lazyframe)
    dr = driver.Builder().with_modules(mod).build()
    with pytest.raises(DataValidationError):
        dr.execute(["invalid_ohlcv_lazyframe"])
