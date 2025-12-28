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
import pyspark.sql as ps
from pyspark.sql import functions as F

from hamilton import htypes
from hamilton.plugins import h_spark


# See https://github.com/dragansah/tpch-dbgen/blob/master/tpch-queries/1.sql
def start_date() -> str:
    return (datetime.date(1998, 12, 1) - datetime.timedelta(days=90)).format("YYYY-MM-DD")


def lineitem_filtered(lineitem: ps.DataFrame, start_date: str) -> ps.DataFrame:
    return lineitem.filter((lineitem.l_shipdate <= start_date))


def disc_price(
    l_extendedprice: pd.Series, l_discount: pd.Series
) -> htypes.column[pd.Series, float]:
    return l_extendedprice * (1 - l_discount)


def charge(
    l_extendedprice: pd.Series, l_discount: pd.Series, l_tax: pd.Series
) -> htypes.column[pd.Series, float]:
    # This could easily depend on the prior one...
    return l_extendedprice * (1 - l_discount) * (1 + l_tax)


@h_spark.with_columns(
    disc_price,
    charge,
    columns_to_pass=["l_extendedprice", "l_discount", "l_tax"],
)
def lineitem_price_charge(lineitem: ps.DataFrame) -> ps.DataFrame:
    return lineitem


def final_data(lineitem_price_charge: ps.DataFrame) -> ps.DataFrame:
    return (
        lineitem_price_charge.groupBy(["l_returnflag", "l_linestatus"])
        .agg(
            F.sum("l_quantity").alias("sum_l_quantity"),
            F.avg("l_quantity").alias("avg_l_quantity"),
            F.sum("l_extendedprice").alias("sum_l_extendedprice"),
            F.avg("l_extendedprice").alias("avg_l_extendedprice"),
            F.sum("disc_price").alias("sum_disc_price"),
            F.sum("charge").alias("sum_charge"),
            F.avg("l_discount").alias("avg_l_discount"),
            F.count("*").alias("count"),
        )
        .orderBy(["l_returnflag", "l_linestatus"])
    ).toPandas()
