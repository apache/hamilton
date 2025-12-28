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

from typing import Tuple

import pandas as pd
from pandas.core.groupby import generic
from sklearn import preprocessing

from hamilton.function_modifiers import parameterize, source


def _label_encoder(col: pd.Series) -> Tuple[preprocessing.LabelEncoder, pd.Series]:
    """Creates an encoder, fits itself on the input, and then transforms the input.

    :param col: the column to encode.
    :return: tuple of fit encoder, and the encoded column.
    """
    encoder = preprocessing.LabelEncoder()
    encoder = encoder.fit(col)
    return encoder, encoder.transform(col)


# this doesn't seem useful at all -- so skipping it
# encoder = preprocessing.LabelEncoder()
# data['id_encode'] = encoder.fit_transform(data['id'])
cols_to_encode = [
    "item_id",
    "dept_id",
    "cat_id",
    "store_id",
    "state_id",
    "event_name_1",
    "event_type_1",
    "event_name_2",
    "event_type_2",
]
mapping = {f"{name}_encoded": dict(column_to_encode=source(name)) for name in cols_to_encode}


@parameterize(**mapping)
def label_encoder(column_to_encode: pd.Series) -> pd.Series:
    """Creates a categorically encoded column from {column_to_encode}.

    :param column_to_encode:
    :return: encoded column
    """
    _, encoded = _label_encoder(column_to_encode)
    return encoded


def grouped_demand(demand: pd.Series) -> generic.SeriesGroupBy:
    """Groups the demands column by id (i.e. the index).

    :param demand:
    :return:
    """
    return demand.groupby(level=0)


def lag_t28(grouped_demand: generic.SeriesGroupBy) -> pd.Series:
    return grouped_demand.transform(lambda x: x.shift(28))


def lag_t29(grouped_demand: generic.SeriesGroupBy) -> pd.Series:
    return grouped_demand.transform(lambda x: x.shift(29))


def lag_t30(grouped_demand: generic.SeriesGroupBy) -> pd.Series:
    return grouped_demand.transform(lambda x: x.shift(30))


def rolling_mean_t7(grouped_demand: generic.SeriesGroupBy) -> pd.Series:
    return grouped_demand.transform(lambda x: x.shift(28).rolling(7).mean())


def rolling_std_t7(grouped_demand: generic.SeriesGroupBy) -> pd.Series:
    return grouped_demand.transform(lambda x: x.shift(28).rolling(7).std())


def rolling_mean_t30(grouped_demand: generic.SeriesGroupBy) -> pd.Series:
    return grouped_demand.transform(lambda x: x.shift(28).rolling(30).mean())


def rolling_mean_t90(grouped_demand: generic.SeriesGroupBy) -> pd.Series:
    return grouped_demand.transform(lambda x: x.shift(28).rolling(90).mean())


def rolling_mean_t180(grouped_demand: generic.SeriesGroupBy) -> pd.Series:
    return grouped_demand.transform(lambda x: x.shift(28).rolling(180).mean())


def rolling_std_t30(grouped_demand: generic.SeriesGroupBy) -> pd.Series:
    return grouped_demand.transform(lambda x: x.shift(28).rolling(30).std())


def grouped_sell_price(sell_price: pd.Series) -> generic.SeriesGroupBy:
    return sell_price.groupby(level=0)


# price features
def lag_price_t1(grouped_sell_price: generic.SeriesGroupBy) -> pd.Series:
    return grouped_sell_price.transform(lambda x: x.shift(1))


def price_change_t1(lag_price_t1: pd.Series, sell_price: pd.Series) -> pd.Series:
    return (lag_price_t1 - sell_price) / lag_price_t1


def rolling_price_max_t365(grouped_sell_price: generic.SeriesGroupBy) -> pd.Series:
    return grouped_sell_price.transform(lambda x: x.shift(1).rolling(365).max())


def price_change_t365(rolling_price_max_t365: pd.Series, sell_price: pd.Series) -> pd.Series:
    return (rolling_price_max_t365 - sell_price) / rolling_price_max_t365


def rolling_price_std_t7(grouped_sell_price: generic.SeriesGroupBy) -> pd.Series:
    return grouped_sell_price.transform(lambda x: x.rolling(7).std())


def rolling_price_std_t30(grouped_sell_price: generic.SeriesGroupBy) -> pd.Series:
    return grouped_sell_price.transform(lambda x: x.rolling(30).std())


# time features
def year(date: pd.Series) -> pd.Series:
    return date.dt.year


def month(date: pd.Series) -> pd.Series:
    return date.dt.month


def week(date: pd.Series) -> pd.Series:
    wk = date.dt.isocalendar().week.astype(int)  # need to cast because lightgbm complains
    return wk


def day(date: pd.Series) -> pd.Series:
    return date.dt.day


def dayofweek(date: pd.Series) -> pd.Series:
    return date.dt.dayofweek
