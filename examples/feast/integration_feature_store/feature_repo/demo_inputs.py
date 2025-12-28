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

"""This module defines example inputs to use with Feast feature retrieval patterns"""

from datetime import datetime

import pandas as pd

HISTORICAL_ENTITY_DF = pd.DataFrame.from_dict(
    {
        # entity's join key -> entity values
        "driver_id": [1001, 1002, 1003],
        # "event_timestamp" (reserved key) -> timestamps
        "event_timestamp": [
            datetime(2021, 4, 12, 10, 59, 42),
            datetime(2021, 4, 12, 8, 12, 10),
            datetime(2021, 4, 12, 16, 40, 26),
        ],
        # (optional) label name -> label values. Feast does not process these
        "label_driver_reported_satisfaction": [1, 5, 3],
        # values we're using for an on-demand transformation
        "val_to_add": [1, 2, 3],
        "val_to_add_2": [10, 20, 30],
    }
)

HISTORICAL_FEATURES = [
    "driver_hourly_stats:conv_rate",
    "driver_hourly_stats:acc_rate",
    "driver_hourly_stats:avg_daily_trips",
    "transformed_conv_rate:conv_rate_plus_val1",
    "transformed_conv_rate:conv_rate_plus_val2",
]


ONLINE_ENTITY_ROWS = [
    # {join_key: entity_value}
    {
        "driver_id": 1001,
        "val_to_add": 1000,
        "val_to_add_2": 2000,
    },
    {
        "driver_id": 1002,
        "val_to_add": 1001,
        "val_to_add_2": 2002,
    },
]

ONLINE_FEATURES = [
    "driver_hourly_stats:acc_rate",
    "transformed_conv_rate:conv_rate_plus_val1",
    "transformed_conv_rate:conv_rate_plus_val2",
]

STREAM_EVENT_DF = pd.DataFrame.from_dict(
    {
        "driver_id": [1001],
        "event_timestamp": [
            datetime.now(),
        ],
        "created": [
            datetime.now(),
        ],
        "conv_rate": [1.0],
        "acc_rate": [1.0],
        "avg_daily_trips": [1000],
    }
)
