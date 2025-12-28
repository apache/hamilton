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

from datetime import datetime

import pandas as pd


def is_male(gender: pd.Series) -> pd.Series:
    return gender == "male"


def is_female(gender: pd.Series) -> pd.Series:
    return gender == "female"


def is_high_roller(budget: pd.Series) -> pd.Series:
    return budget > 100


def age_normalized(age: pd.Series, age_mean: float, age_stddev: float) -> pd.Series:
    return (age - age_mean) / age_stddev


def time_since_last_login(execution_time: datetime, last_logged_in: pd.Series) -> pd.Series:
    return execution_time - last_logged_in
