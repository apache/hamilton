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

from typing import Dict

import map_transforms
import pandas as pd
import pyspark.sql as ps
from pyspark.sql.functions import col, mean, stddev

from hamilton.function_modifiers import extract_fields
from hamilton.plugins import h_spark


def spark_session() -> ps.SparkSession:
    """Pyspark session to load up when starting.
    You can also pass it in if you so choose.

    :return:
    """
    return ps.SparkSession.builder.master("local[1]").getOrCreate()


def base_df(spark_session: ps.SparkSession) -> ps.DataFrame:
    """Dummy function showing how to wire through loading data.
    Note you can use @load_from (although our spark data loaders are limited now).

    :return: A dataframe with spend and signups columns.
    """
    pd_df = pd.DataFrame(
        {
            "spend": [
                10,
                10,
                20,
                40,
                40,
                50,
                60,
                70,
                90,
                100,
                70,
                80,
                90,
                100,
                110,
                120,
                130,
                140,
                150,
                160,
            ],
            "signups": [
                1,
                10,
                50,
                100,
                200,
                400,
                600,
                800,
                1000,
                1200,
                1400,
                1600,
                1800,
                2000,
                2200,
                2400,
                2600,
                2800,
                3000,
                3200,
            ],
        }
    )
    return spark_session.createDataFrame(pd_df)


@extract_fields(
    {
        "spend_mean": float,
        "spend_std_dev": float,
    }
)
def spend_statistics(base_df: ps.DataFrame) -> Dict[str, float]:
    """Computes the mean and standard deviation of the spend column.
    Note that this is a blocking (collect) operation,
    but it doesn't have to be if you use an aggregation. In that case
    you'd just add the column to the dataframe and refer to it downstream,
    by expanding `columns_to_pass` in `with_mapped_data`.

    :param base_df: Base dataframe with spend and signups columns.
    :return: A dictionary with the mean and standard deviation of the spend column.
    """
    df_stats = base_df.select(
        mean(col("spend")).alias("mean"), stddev(col("spend")).alias("std")
    ).collect()

    return {
        "spend_mean": df_stats[0]["mean"],
        "spend_std_dev": df_stats[0]["std"],
    }


@h_spark.with_columns(
    map_transforms,
    columns_to_pass=["spend", "signups"],
)
def with_mapped_data(base_df: ps.DataFrame) -> ps.DataFrame:
    """Applies all the transforms in map_transforms

    :param base_df:
    :return:
    """
    return base_df


def final_result(with_mapped_data: ps.DataFrame) -> pd.DataFrame:
    """Computes the final result. You could always just output the pyspark
    dataframe, but we'll collect it and make it a pandas dataframe.

    :param base_df: Base dataframe with spend and signups columns.
    :return: A dataframe with the final result.
    """
    return with_mapped_data.toPandas()
