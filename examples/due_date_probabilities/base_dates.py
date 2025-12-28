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

import pandas as pd


def due_date(start_date: datetime.datetime) -> datetime.datetime:
    """The due date is start_date + 40 weeks. Start date is the date of the expecting mother's last period"""
    return start_date + datetime.timedelta(weeks=40)


def possible_dates(
    due_date: datetime.datetime,
    buffer_before_due_date: int = 8 * 7,
    buffer_after_due_date: int = 4 * 7,
) -> pd.Series:
    """Gets all the reasonably possible dates (-8 weeks, + 4 weeks) of delivery"""
    idx = pd.date_range(
        due_date - datetime.timedelta(days=buffer_before_due_date),
        due_date + datetime.timedelta(days=buffer_after_due_date),
    )
    return pd.Series(data=idx, index=idx)
