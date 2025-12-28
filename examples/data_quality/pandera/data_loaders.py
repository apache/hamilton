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

"""
This module defines data loading logic that we'd like to apply.

We could put data quality checks here - but we leave them as an exercise for the reader.

Note:
    (1) to handle running on dask, ray, and spark, you will see some `@config.when*` decorators, which will
    determine whether this function should exist or not depending on some configuration passed in.
    (2) instead of @config.when* we could instead move these functions into specific independent modules, and then in
    the driver choose which one to use for the DAG. For the purposes of this example, we decided one file is simpler.
"""

from typing import List

import pandas as pd

from hamilton.function_modifiers import config, extract_columns, load_from, source, value

data_columns = [
    "id",
    "reason_for_absence",
    "month_of_absence",
    "day_of_the_week",
    "seasons",
    "transportation_expense",
    "distance_from_residence_to_work",
    "service_time",
    "age",
    "work_load_average_per_day",
    "hit_target",
    "disciplinary_failure",
    "education",
    "son",
    "social_drinker",
    "social_smoker",
    "pet",
    "weight",
    "height",
    "body_mass_index",
    "absenteeism_time_in_hours",
]


def _sanitize_columns(df_columns: List[str]) -> List[str]:
    """Renames columns to be valid hamilton names -- and lower cases them.

    :param df_columns: the current column names.
    :return: sanitize column names that work with Hamilton
    """
    return [c.strip().replace("/", "_per_").replace(" ", "_").lower() for c in df_columns]


@config.when_not_in(execution=["dask", "spark"])
@extract_columns(*data_columns)
@load_from.csv(path=source("location"), sep=value(";"))
def raw_data__base(df: pd.DataFrame) -> pd.DataFrame:
    """Extracts the raw data, renames the columns to be valid python variable names, and assigns an index.
    :param location: the location to load from
    :return:
    """

    # rename columns to be valid hamilton names -- and lower case it
    df.columns = _sanitize_columns(df.columns)
    # create proper index -- ID-Month-Day;
    index = (
        df["id"].astype(str)
        + "-"
        + df["month_of_absence"].astype(str)
        + "-"
        + df["day_of_the_week"].astype(str)
    )
    df.index = index
    return df


@config.when(execution="dask")
@extract_columns(*data_columns)
def raw_data__dask(location: str, block_size: str = "10KB") -> pd.DataFrame:
    """Extracts the raw data, renames the columns to be valid python variable names, and assigns an index.
    :param location: the location to load from
    :param block_size: size at which to partition the data. 10KB here is only to ensure our small data set is partitioned.
    :return: dask dataframe
    """
    from dask import dataframe

    df = dataframe.read_csv(location, sep=";", blocksize=block_size)
    # rename columns to be valid hamilton names -- and lower case it
    df.columns = _sanitize_columns(df.columns)
    # create proper index -- ID-Month-Day;
    df.index = (
        df["id"].astype(str)
        + "-"
        + df["month_of_absence"].astype(str)
        + "-"
        + df["day_of_the_week"].astype(str)
    )
    return df


@config.when(execution="spark")
@extract_columns("index_col", *data_columns)
@load_from.csv(path=source("location"), sep=value(";"))
def raw_data__spark(df: pd.DataFrame) -> pd.DataFrame:
    """Extracts the raw data, renames the columns to be valid python variable names, and assigns an index.
    :param location: the location to load from
    :param number_partitions: number of partitions to partition the data for dask.
    :return: dask dataframe
    """
    # rename columns to be valid hamilton names -- and lower case it
    df.columns = _sanitize_columns(df.columns)
    # create proper index -- ID-Month-Day;
    index = (
        df["id"].astype(str)
        + "-"
        + df["month_of_absence"].astype(str)
        + "-"
        + df["day_of_the_week"].astype(str)
    )
    df.index = index
    df["index_col"] = df.index
    # this is a quick way to do this
    import pyspark.pandas as ps

    ps_df = ps.from_pandas(df)
    return ps_df


if __name__ == "__main__":
    # this is here as a quick way to check that things are working.
    d = raw_data__base("Absenteeism_at_work.csv")
    print(d.to_string())
