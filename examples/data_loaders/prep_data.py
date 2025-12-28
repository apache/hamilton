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

from hamilton.function_modifiers import does, extract_columns, parameterize, source, value


def _sum_series(**series):
    return sum(series.values())


@extract_columns(
    "facebook_spend",
    "twitter_spend",
    "tv_spend",
    "youtube_spend",
    "radio_spend",
    "billboards_spend",
    "womens_churn",
    "mens_churn",
    "womens_signups",
    "mens_signups",
)
def joined_data(spend: pd.DataFrame, signups: pd.DataFrame, churn: pd.DataFrame) -> pd.DataFrame:
    spend = spend.set_index("date").rename(columns=lambda col: col + "_spend")
    churn = churn.set_index("date").rename(columns=lambda col: col + "_churn")
    signups = signups.set_index("date").rename(columns=lambda col: col + "_signups")
    return pd.concat([spend, churn, signups], axis=1)


@does(_sum_series)
def total_marketing_spend(
    facebook_spend: pd.Series,
    twitter_spend: pd.Series,
    tv_spend: pd.Series,
    youtube_spend: pd.Series,
    radio_spend: pd.Series,
    billboards_spend: pd.Series,
) -> pd.Series:
    pass


@does(_sum_series)
def total_signups(mens_signups: pd.Series, womens_signups: pd.Series) -> pd.Series:
    pass


@does(_sum_series)
def total_churn(mens_churn: pd.Series, womens_churn: pd.Series) -> pd.Series:
    pass


def total_customers(total_signups: pd.Series, total_churn: pd.Series) -> pd.Series:
    customer_deltas = total_signups + total_churn
    return customer_deltas.cumsum()


def acquisition_cost(total_marketing_spend: pd.Series, total_signups: pd.Series) -> pd.Series:
    return total_marketing_spend / total_signups


@parameterize(
    twitter_spend_smoothed={"lookback_days": value(7), "spend": source("twitter_spend")},
    facebook_spend_smoothed={"lookback_days": value(7), "spend": source("facebook_spend")},
    radio_spend_smoothed={"lookback_days": value(21), "spend": source("radio_spend")},
    tv_spend_smoothed={"lookback_days": value(21), "spend": source("tv_spend")},
    billboards_spend_smoothed={"lookback_days": value(7), "spend": source("billboards_spend")},
    youtube_spend_smoothed={"lookback_days": value(7), "spend": source("twitter_spend")},
)
def spend_smoothed(lookback_days: int, spend: pd.Series) -> pd.Series:
    """{spend} smoothed by {lookback_days}. Might want to smooth different ad spends differently,
    figuring that it takes different amounts of time to get to the customer. A cheap hack at determining
    auto-correlation of a series -- this should be a parameter in a model,
    but this is to demonstrate the framework

    :param lookback_days: Days to smooth over
    :param spend: Spend source
    :return:
    """
    return spend.rolling(window=lookback_days).mean().fillna(0)
