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

import datetime
from typing import Dict, List, Union

import polars as pl
from hamilton_sdk.tracking import dataframe_stats as dfs


def data_type(col: pl.Series) -> str:
    return str(col.dtype)


def count(col: pl.Series) -> int:
    return len(col)


def missing(col: pl.Series) -> int:
    """Mimics what we do for pandas."""
    try:
        # only for floats does is_nan() work.
        nan_count = col.is_nan().sum()
    except pl.InvalidOperationError:
        nan_count = 0
    return col.is_null().sum() + nan_count


def zeros(col: pl.Series) -> int:
    try:
        result = col.eq(0)
    except TypeError:
        return 0
    except ValueError:
        # e.g. comparing datetime
        return 0
    if str(result) == "NotImplemented":
        return 0
    return result.sum()


def min(col: pl.Series) -> Union[float, int]:
    return col.min()


def max(col: pl.Series) -> Union[float, int]:
    return col.max()


def mean(col: pl.Series) -> float:
    return col.mean()


def std(col: pl.Series) -> float:
    return col.std()


def quantile_cuts() -> List[float]:
    return [0.10, 0.25, 0.50, 0.75, 0.90]


def quantiles(col: pl.Series, quantile_cuts: List[float]) -> Dict[float, float]:
    result = {}
    try:
        for q in quantile_cuts:
            result[q] = col.quantile(q)
    except pl.InvalidOperationError:
        return {}
    return result


def histogram(col: pl.Series, num_hist_bins: int = 10) -> Dict[str, int]:
    """This is different than pandas... requires polars 0.20+"""
    if all(col.is_null()):
        return {}
    try:
        hist_dict = col.drop_nulls().hist(bin_count=num_hist_bins).to_dict(as_series=False)
    except pl.InvalidOperationError:
        # happens for Date data types. TODO: convert them to numeric so we can get a histogram.
        return {}
    return dict(zip(hist_dict["category"], hist_dict["count"]))


def numeric_column_stats(
    name: str,
    position: int,
    data_type: str,
    count: int,
    missing: int,
    zeros: int,
    min: Union[float, int],
    max: Union[float, int],
    mean: float,
    std: float,
    quantiles: Dict[float, float],
    histogram: Dict[str, int],
) -> dfs.NumericColumnStatistics:
    return dfs.NumericColumnStatistics(
        name=name,
        pos=position,
        data_type=data_type,
        count=count,
        missing=missing,
        zeros=zeros,
        min=min,
        max=max,
        mean=mean,
        std=std,
        quantiles=quantiles,
        histogram=histogram,
    )


def datetime_column_stats(
    name: str,
    position: int,
    data_type: str,
    count: int,
    missing: int,
    zeros: int,
    min: Union[float, int],
    max: Union[float, int],
    mean: float,
    quantiles: Dict[float, float],
    histogram: Dict[str, int],
) -> dfs.DatetimeColumnStatistics:
    # TODO: push these conversions into Hamilton functions.
    min = min.isoformat() if isinstance(min, (pl.Date, pl.Datetime, datetime.date)) else min
    max = max.isoformat() if isinstance(max, (pl.Date, pl.Datetime, datetime.date)) else max
    mean = mean.isoformat() if isinstance(mean, (pl.Date, pl.Datetime, datetime.date)) else mean
    quantiles = {
        q: v if not isinstance(v, pl.Datetime) else v.isoformat() for q, v in quantiles.items()
    }
    return dfs.DatetimeColumnStatistics(
        name=name,
        pos=position,
        data_type=data_type,
        count=count,
        missing=missing,
        zeros=zeros,
        min=min,
        max=max,
        mean=mean,
        std=0.0,
        quantiles=quantiles,
        histogram=histogram,
    )


def str_len(col: pl.Series) -> pl.Series:
    return col.str.len_chars()


def avg_str_len(str_len: pl.Series) -> float:
    return str_len.mean()


def std_str_len(str_len: pl.Series) -> float:
    return str_len.std()


def empty(col: pl.Series) -> int:
    return (col == "").sum()


def value_counts(col: pl.Series) -> pl.DataFrame:
    v_counts = col.value_counts()
    if "counts" in v_counts.columns:
        return v_counts.sort(by="counts", descending=True)
    elif "count" in v_counts.columns:
        return v_counts.sort(by="count", descending=True)
    else:
        return v_counts


def domain(value_counts: pl.DataFrame) -> Dict[str, int]:
    result = value_counts.to_dict(as_series=False)
    if "counts" in result:
        counter_column = "counts"
    elif "count" in result:
        counter_column = "count"
    else:
        counter_column = None
    col_name = [k for k in result.keys() if k != counter_column][0]
    return dict(zip(result[col_name], result.get(counter_column)))


def top_value(domain: Dict[str, int]) -> str:
    return next(iter(domain.keys()))


def top_freq(domain: Dict[str, int]) -> int:
    return next(iter(domain.values()))


def unique(col: pl.Series) -> int:
    return len(col.unique())


def category_column_stats(
    name: str,
    position: int,
    data_type: str,
    count: int,
    missing: int,
    empty: int,
    domain: Dict[str, int],
    top_value: str,
    top_freq: int,
    unique: int,
) -> dfs.CategoryColumnStatistics:
    return dfs.CategoryColumnStatistics(
        name=name,
        pos=position,
        data_type=data_type,
        count=count,
        missing=missing,
        empty=empty,
        domain=domain,
        top_value=top_value,
        top_freq=top_freq,
        unique=unique,
    )


def string_column_stats(
    name: str,
    position: int,
    data_type: str,
    avg_str_len: float,
    std_str_len: float,
    count: int,
    missing: int,
    empty: int,
) -> dfs.StringColumnStatistics:
    return dfs.StringColumnStatistics(
        name=name,
        pos=position,
        data_type=data_type,
        avg_str_len=avg_str_len,
        std_str_len=std_str_len,
        count=count,
        missing=missing,
        empty=empty,
    )


def boolean_column_stats(
    name: str,
    position: int,
    data_type: str,
    count: int,
    missing: int,
    zeros: int,
) -> dfs.BooleanColumnStatistics:
    return dfs.BooleanColumnStatistics(
        name=name,
        pos=position,
        data_type=data_type,
        count=count,
        missing=missing,
        zeros=zeros,
    )


def unhandled_column_stats(
    name: str,
    position: int,
    data_type: str,
    count: int,
    missing: int,
) -> dfs.UnhandledColumnStatistics:
    return dfs.UnhandledColumnStatistics(
        name=name,
        pos=position,
        data_type=data_type,
        count=count,
        missing=missing,
    )


# if __name__ == "__main__":
# pass
