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
import pyspark.sql as ps
from pyspark.sql import functions as F

from hamilton import htypes
from hamilton.plugins import h_spark

# see # See # See https://github.com/dragansah/tpch-dbgen/blob/master/tpch-queries/12.sql


def lineitems_joined_with_orders(lineitem: ps.DataFrame, orders: ps.DataFrame) -> ps.DataFrame:
    return lineitem.join(orders, lineitem.l_orderkey == orders.o_orderkey)


def start_date() -> str:
    return "1995-01-01"


def end_date() -> str:
    return "1996-12-31"


def filtered_data(
    lineitems_joined_with_orders: ps.DataFrame, start_date: str, end_date: str
) -> ps.DataFrame:
    return lineitems_joined_with_orders.filter(
        (lineitems_joined_with_orders.l_shipmode.isin("MAIL", "SHIP"))
        & (lineitems_joined_with_orders.l_commitdate < lineitems_joined_with_orders.l_receiptdate)
        & (lineitems_joined_with_orders.l_shipdate < lineitems_joined_with_orders.l_commitdate)
        & (lineitems_joined_with_orders.l_receiptdate >= start_date)
        & (lineitems_joined_with_orders.l_receiptdate < end_date)
    )


def high_priority(o_orderpriority: pd.Series) -> htypes.column[pd.Series, int]:
    return (o_orderpriority == "1-URGENT") | (o_orderpriority == "2-HIGH")


def low_priority(o_orderpriority: pd.Series) -> htypes.column[pd.Series, int]:
    return (o_orderpriority != "1-URGENT") & (o_orderpriority != "2-HIGH")


@h_spark.with_columns(high_priority, low_priority, columns_to_pass=["o_orderpriority"])
def with_priorities(filtered_data: ps.DataFrame) -> ps.DataFrame:
    return filtered_data


def shipmode_aggregated(with_priorities: ps.DataFrame) -> ps.DataFrame:
    return with_priorities.groupBy("l_shipmode").agg(
        F.sum("high_priority").alias("sum_high"),
        F.sum("low_priority").alias("sum_low"),
    )


def final_data(shipmode_aggregated: ps.DataFrame) -> pd.DataFrame:
    return shipmode_aggregated.toPandas()
