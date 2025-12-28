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
import pandas as pd

from hamilton.function_modifiers import extract_columns, save_to, source

TRIPS_SOURCE_COLUMNS = [
    "event_timestamp",
    "driver_id",
    "rider_id",
    "trip_dist",
    "created",
]


@extract_columns(*TRIPS_SOURCE_COLUMNS)
def trips_raw(trips_raw_path: str) -> pd.DataFrame:
    """Load the driver dataset"""
    df = pd.read_parquet(trips_raw_path)
    df = df.sort_values(by="event_timestamp")
    return df


def day_of_week(event_timestamp: pd.Series) -> pd.Series:
    """Encode day of the week as int"""
    return pd.Series(
        event_timestamp.dt.day_of_week, name="day_of_week", index=event_timestamp.index
    )


def is_weekend(day_of_week: pd.Series) -> pd.Series:
    weekend = np.where(day_of_week >= 5, 1, 0)
    return pd.Series(weekend, name="is_weekend", index=day_of_week.index)


def month(event_timestamp: pd.Series) -> pd.Series:
    """Encode month of the trip as int"""
    return pd.Series(event_timestamp.dt.month, name="month", index=event_timestamp.index)


def avg_trip_dist_rolling_3h(trip_dist: pd.Series, event_timestamp: pd.Series) -> pd.Series:
    """Compute the rolling 3H mean trip dist"""
    df = pd.concat([trip_dist, event_timestamp], axis=1)
    agg = df.rolling("3H", on="event_timestamp")["trip_dist"].mean()
    return pd.Series(agg, name="avg_trip_dist_rolling_3h", index=event_timestamp.index)


def max_trip_dist_rolling_3h(trip_dist: pd.Series, event_timestamp: pd.Series) -> pd.Series:
    """Compute the rolling 3H max trip dist"""
    df = pd.concat([trip_dist, event_timestamp], axis=1)
    agg = df.rolling("3H", on="event_timestamp")["trip_dist"].max()
    return pd.Series(agg, name="max_trip_dist_rolling_3h", index=event_timestamp.index)


def min_trip_dist_rolling_3h(trip_dist: pd.Series, event_timestamp: pd.Series) -> pd.Series:
    """Compute the rolling 3H min trip dist"""
    df = pd.concat([trip_dist, event_timestamp], axis=1)
    agg = df.rolling("3H", on="event_timestamp")["trip_dist"].min()
    return pd.Series(agg, name="min_trip_dist_rolling_3h", index=event_timestamp.index)


def percentile_dist_rolling_3h(trip_dist: pd.Series, event_timestamp: pd.Series) -> pd.Series:
    """Compute the rolling 3H percentile trip dist"""
    df = pd.concat([trip_dist, event_timestamp], axis=1)
    agg = df.rolling("3H", on="event_timestamp")["trip_dist"].rank(pct=True)
    return pd.Series(agg, name="percentile_trip_dist_rolling_3h", index=event_timestamp.index)


@save_to.parquet(path=source("trips_stats_3h_path"), output_name_="save_trips_stats_3h")
def trips_stats_3h(
    event_timestamp: pd.Series,
    driver_id: pd.Series,
    rider_id: pd.Series,
    trip_dist: pd.Series,
    day_of_week: pd.Series,
    is_weekend: pd.Series,
    month: pd.Series,
    avg_trip_dist_rolling_3h: pd.Series,
    max_trip_dist_rolling_3h: pd.Series,
    min_trip_dist_rolling_3h: pd.Series,
    percentile_dist_rolling_3h: pd.Series,
) -> pd.DataFrame:
    """Global trip statistics over rolling 3h"""
    df = pd.concat(
        [
            event_timestamp,
            driver_id,
            rider_id,
            trip_dist,
            day_of_week,
            is_weekend,
            month,
            avg_trip_dist_rolling_3h,
            max_trip_dist_rolling_3h,
            min_trip_dist_rolling_3h,
            percentile_dist_rolling_3h,
        ],
        axis=1,
    )
    return df
