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
import unique_users

from hamilton.function_modifiers import subdag, value


def website_interactions() -> pd.DataFrame:
    """Gives event-driven data with a series

    :return: Some mock event data.
    """
    data = [
        ("20220901-14:00:00", 1, "US"),
        ("20220901-18:30:00", 2, "US"),
        ("20220901-19:00:00", 1, "US"),
        ("20220902-08:00:00", 3, "US"),
        ("20220903-16:00:00", 1, "US"),
        ("20220907-13:00:00", 4, "US"),
        ("20220910-14:00:00", 1, "US"),
        ("20220911-12:00:00", 3, "US"),
        ("20220914-11:00:00", 1, "US"),
        ("20220915-07:30:00", 2, "US"),
        ("20220916-06:00:00", 1, "US"),
        ("20220917-16:00:00", 2, "US"),
        ("20220920-17:00:00", 5, "US"),
        ("20220922-09:30:00", 2, "US"),
        ("20220922-10:00:00", 1, "US"),
        ("20220924-07:00:00", 6, "US"),
        ("20220924-08:00:00", 1, "US"),
        ("20220925-21:00:00", 1, "US"),
        ("20220926-15:30:00", 2, "US"),
        ("20220901-14:00:00", 7, "CA"),
        ("20220901-18:30:00", 8, "CA"),
        ("20220901-19:00:00", 9, "CA"),
        ("20220902-08:00:00", 7, "CA"),
        ("20220903-16:00:00", 10, "CA"),
        ("20220907-13:00:00", 9, "CA"),
        ("20220910-14:00:00", 8, "CA"),
        ("20220911-12:00:00", 11, "CA"),
        ("20220914-11:00:00", 12, "CA"),
        ("20220915-07:30:00", 7, "CA"),
        ("20220916-06:00:00", 9, "CA"),
        ("20220917-16:00:00", 10, "CA"),
        ("20220920-17:00:00", 7, "CA"),
        ("20220922-09:30:00", 11, "CA"),
        ("20220922-10:00:00", 8, "CA"),
        ("20220924-07:00:00", 9, "CA"),
        ("20220924-08:00:00", 10, "CA"),
        ("20220925-21:00:00", 13, "CA"),
        ("20220926-15:30:00", 14, "CA"),
    ]
    df = (
        pd.DataFrame(data, columns=["timestamp", "user_id", "region"])
        .set_index("timestamp")
        .sort_index()
    )
    df.index = pd.DatetimeIndex(df.index)
    return df


@subdag(
    unique_users,
    inputs={"grain": value("day")},
    config={"region": "US"},
)
def daily_unique_users_US(unique_users: pd.Series) -> pd.Series:
    return unique_users


@subdag(
    unique_users,
    inputs={"grain": value("week")},
    config={"region": "US"},
)
def weekly_unique_users_US(unique_users: pd.Series) -> pd.Series:
    return unique_users


@subdag(
    unique_users,
    inputs={"grain": value("month")},
    config={"region": "US"},
)
def monthly_unique_users_US(unique_users: pd.Series) -> pd.Series:
    return unique_users


@subdag(
    unique_users,
    inputs={"grain": value("day")},
    config={"region": "CA"},
)
def daily_unique_users_CA(unique_users: pd.Series) -> pd.Series:
    return unique_users


@subdag(
    unique_users,
    inputs={"grain": value("week")},
    config={"region": "CA"},
)
def weekly_unique_users_CA(unique_users: pd.Series) -> pd.Series:
    return unique_users


@subdag(
    unique_users,
    inputs={"grain": value("month")},
    config={"region": "CA"},
)
def monthly_unique_users_CA(unique_users: pd.Series) -> pd.Series:
    return unique_users
