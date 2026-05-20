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

"""A small marketing dataflow we will test.

Each public function below becomes a node in the Hamilton DAG. Functions are
ordinary Python -- nothing about them depends on the driver -- which is what
makes them straightforward to unit-test.
"""

import pandas as pd


def signups(raw_signups: pd.Series) -> pd.Series:
    """Drop the first row (which is always a header sentinel in our source)."""
    return raw_signups.iloc[1:].reset_index(drop=True)


def spend(raw_spend: pd.Series) -> pd.Series:
    """Drop the first row to align with `signups`."""
    return raw_spend.iloc[1:].reset_index(drop=True)


def avg_3wk_spend(spend: pd.Series) -> pd.Series:
    """Rolling 3-week average spend."""
    return spend.rolling(3).mean()


def spend_per_signup(spend: pd.Series, signups: pd.Series) -> pd.Series:
    """Cost per signup, in dollars."""
    return spend / signups


def spend_mean(spend: pd.Series) -> float:
    """Mean of the spend column."""
    return spend.mean()


def spend_zero_mean(spend: pd.Series, spend_mean: float) -> pd.Series:
    """Spend with the mean subtracted off."""
    return spend - spend_mean


def spend_std_dev(spend: pd.Series) -> float:
    """Standard deviation of the spend column."""
    return spend.std()


def spend_zero_mean_unit_variance(spend_zero_mean: pd.Series, spend_std_dev: float) -> pd.Series:
    """Standard-scaled spend (zero mean, unit variance)."""
    return spend_zero_mean / spend_std_dev
