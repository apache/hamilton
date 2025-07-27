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

from typing import Dict, List, Union

import pandas as pd
from hamilton_sdk.tracking import dataframe_stats as dfs


def data_type(col: pd.Series) -> str:
    return str(col.dtype)


def count(col: pd.Series) -> int:
    return len(col)


def missing(col: pd.Series) -> int:
    return col.isna().sum()


def zeros(col: pd.Series) -> int:
    return (col == 0).sum()


def min(col: pd.Series) -> Union[float, int]:
    return col.min()


def max(col: pd.Series) -> Union[float, int]:
    return col.max()


def mean(col: pd.Series) -> float:
    return col.mean()


def std(col: pd.Series) -> float:
    return col.std()


def quantile_cuts() -> List[float]:
    return [0.10, 0.25, 0.50, 0.75, 0.90]


def quantiles(col: pd.Series, quantile_cuts: List[float]) -> Dict[float, float]:
    return col.quantile(quantile_cuts).to_dict()


def histogram(col: pd.Series, num_hist_bins: int = 10) -> Dict[str, int]:
    try:
        hist_counts = (
            col.value_counts(
                bins=num_hist_bins,
            )
            .sort_index()
            .to_dict()
        )
    except ValueError:
        return {}
    except AttributeError:
        return {}
    return {str(interval): interval_value for interval, interval_value in hist_counts.items()}


def numeric_column_stats(
    name: Union[str, int],
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
    name: Union[str, int],
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
) -> dfs.DatetimeColumnStatistics:
    # TODO: push these conversions into Hamilton functions.
    min = min.isoformat() if isinstance(min, pd.Timestamp) else min
    max = max.isoformat() if isinstance(max, pd.Timestamp) else max
    mean = mean.isoformat() if isinstance(mean, pd.Timestamp) else mean
    std = std.isoformat() if isinstance(std, pd.Timedelta) else std
    quantiles = {
        q: v if not isinstance(v, pd.Timestamp) else v.isoformat() for q, v in quantiles.items()
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
        std=std,
        quantiles=quantiles,
        histogram=histogram,
    )


def str_len(col: pd.Series) -> pd.Series:
    return col.str.len()


def avg_str_len(str_len: pd.Series) -> float:
    return str_len.mean()


def std_str_len(str_len: pd.Series) -> float:
    return str_len.std()


def empty(col: pd.Series) -> int:
    return (col == "").sum()


def value_counts(col: pd.Series) -> pd.Series:
    return col.value_counts()


def domain(value_counts: pd.Series) -> Dict[str, int]:
    return value_counts.to_dict()


def top_value(value_counts: pd.Series) -> str:
    return value_counts.index[0]


def top_freq(value_counts: pd.Series) -> int:
    return value_counts.iloc[0]


def unique(col: pd.Series) -> int:
    return len(col.unique())


def category_column_stats(
    name: Union[str, int],
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
    name: Union[str, int],
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
    name: Union[str, int],
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
    name: Union[str, int],
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
