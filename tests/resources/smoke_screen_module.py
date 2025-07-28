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

"""A module that has a bunch of features.
This enables us to test out all capabilities in a smoke test, which is
especially helpful for adding complex graphadapters.
This aims to include the following features:

1. @config.when() ✅
2. @parameterize (arguments for both value and source) ✅
3. @extract_columns ✅
4. @extract_fields  ✅
5. @does ✅
6. @tag ✅
7. @check_output (with default args) ✅

Note this will also have a simple API to work with:

1. Required inputs = start_date/end_date, 'YYYYMMDD'
2. Required config = {'region' : 'US'/'CA'}
3. Four outputs, all pd.Series:
    raw_acquisition_cost
    pessimistic_net_acquisition_cost
    neutral_net_acquisition_cost
    optimistic_net_acquisition_cost
"""

from typing import Dict

import numpy as np
import pandas as pd

from hamilton.function_modifiers import (
    check_output,
    config,
    does,
    extract_columns,
    extract_fields,
    parameterize,
    source,
    tag,
    value,
)


def start_date(date_range: Dict[str, str]) -> str:
    return date_range["start_date"]


def end_date(date_range: Dict[str, str]) -> str:
    return date_range["end_date"]


def _identity(**kwargs: int) -> int:
    """The API for this is suboptimal but this will serve for testing."""
    return list(kwargs.values())[0]


@extract_fields(fields={"us_churn": int, "ca_churn": dict})
def weekly_churn() -> Dict[str, int]:
    """Weekly churn for both regions. A little contrived so we can use extract_fields"""
    return {"us_churn": 3, "ca_churn": 2}


@config.when(region="US")
@does(_identity)
def weekly_churn_base_rate__US(us_churn: int) -> int:
    pass


@config.when(region="CA")
@does(_identity)
def weekly_churn_base_rate__CA(ca_churn: int) -> int:
    pass


@config.when_not(pandas_on_spark=True)
@extract_columns("spend", "signups", "weeks")
def spend_and_signups_source__pd(start_date: str, end_date: str) -> pd.DataFrame:
    """Yields `spend`, `signups`, and 'weeks' (the spine) in a single dataframe.
    All of this is obviously dummy data.
    """
    index = pd.DatetimeIndex(pd.date_range(start=start_date, end=end_date, freq="7d"))
    df_out = pd.DataFrame(data=dict(weeks=index, counts=list(range(len(index)))))
    df_out["spend"] = df_out.apply(lambda row: 100 + min((row.counts + 1) * 5, 250), axis=1)
    df_out["signups"] = df_out.apply(lambda row: 20 * min(row.counts + 1, 100), axis=1)
    return df_out[["spend", "signups", "weeks"]]


@config.when(pandas_on_spark=True)
@extract_columns("spend", "signups", "weeks")
def spend_and_signups_source__ps(start_date: str, end_date: str) -> pd.DataFrame:
    """Yields `spend`, `signups`, and 'weeks' (the spine) in a single dataframe.
    All of this is obviously dummy data.
    """
    # This is just me being lazy -- need to dig into pandas on spark to figure out the best way to instantiate it
    # But for now I can just re-use the code above.
    pd_df = spend_and_signups_source__pd(start_date=start_date, end_date=end_date)
    import pyspark.pandas as ps

    return ps.DataFrame(pd_df)


@check_output(
    importance="fail",
    range=(-1000, 10000),  # Could be negative but never below 100
    data_type=np.float64,
)
@parameterize(
    net_signups_pessimistic={"optimism_adjustment": value(0.5)},
    net_signups_neutral={"optimism_adjustment": value(1.0)},
    net_signups_optimistic={"optimism_adjustment": value(2)},
)
def net_signups(
    signups: pd.Series, weekly_churn_base_rate: int, optimism_adjustment: float
) -> pd.Series:
    return signups - weekly_churn_base_rate * 1 / optimism_adjustment


@parameterize(
    raw_acquisition_cost={"signups_source": source("signups")},
    pessimistic_net_acquisition_cost={"signups_source": source("net_signups_pessimistic")},
    neutral_net_acquisition_cost={"signups_source": source("net_signups_neutral")},
    optimistic_net_acquisition_cost={"signups_source": source("net_signups_optimistic")},
)
@tag(final_output="true")
def acquisition_cost(signups_source: pd.Series, spend: pd.Series) -> pd.Series:
    return spend / signups_source


def _prefix_dict_values(prefix: str, dict_to_prefix: Dict[str, str]):
    """Smoke screen tests to ensure we can work with complex types.
    Contrived relationship to the theme...

    :param prefix: Some string
    :param dict_to_prefix: Some dict of string to string
    :return: Dict b with a concated to keys
    """
    return {k: prefix + v for k, v in dict_to_prefix.items()}


def date_prefix() -> str:
    return "date_"


@does(_prefix_dict_values, prefix="date_prefix", dict_to_prefix="date_range")
def prefixed_date_info(date_prefix: str, date_range: Dict[str, str]) -> Dict[str, str]:
    """Smoke screen tests to ensure we can work with complex types."""


def series_with_start_date_end_date(
    weeks: pd.Series, prefixed_date_info: Dict[str, str]
) -> pd.Series:
    """Smoke screen tests to ensure we can work with complex types."""
    return weeks.apply(
        lambda x: prefixed_date_info["start_date"] + "_" + prefixed_date_info["end_date"]
    )
