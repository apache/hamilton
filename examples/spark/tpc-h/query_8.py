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
import pyspark.sql.functions as F

# See # See https://github.com/dragansah/tpch-dbgen/blob/master/tpch-queries/8.sql
from hamilton import htypes
from hamilton.plugins import h_spark


def start_date() -> str:
    return "1995-01-01"


def end_date() -> str:
    return "1996-12-31"


def america(region: ps.DataFrame) -> ps.DataFrame:
    return region.filter(F.col("r_name") == "AMERICA")


def american_nations(nation: ps.DataFrame, america: ps.DataFrame) -> ps.DataFrame:
    return nation.join(america, nation.n_regionkey == america.r_regionkey).select(["n_nationkey"])


def american_customers(customer: ps.DataFrame, american_nations: ps.DataFrame) -> ps.DataFrame:
    return customer.join(american_nations, customer.c_nationkey == american_nations.n_nationkey)


def american_orders(orders: ps.DataFrame, american_customers: ps.DataFrame) -> ps.DataFrame:
    return orders.join(american_customers, orders.o_custkey == american_customers.c_custkey)


def order_data_augmented(
    american_orders: ps.DataFrame,
    lineitem: ps.DataFrame,
    supplier: ps.DataFrame,
    nation: ps.DataFrame,
    part: ps.DataFrame,
) -> ps.DataFrame:
    d = lineitem.join(part, lineitem.l_partkey == part.p_partkey).drop("n_nation", "n_nationkey")
    d = d.join(american_orders.drop("n_nationkey"), d.l_orderkey == american_orders.o_orderkey)
    d = d.join(supplier, d.l_suppkey == supplier.s_suppkey)
    d = d.join(nation, d.s_nationkey == nation.n_nationkey)
    return d


def order_data_filtered(
    order_data_augmented: ps.DataFrame,
    start_date: str,
    end_date: str,
    p_type: str = "ECONOMY ANODIZED STEEL",
) -> ps.DataFrame:
    return order_data_augmented.filter(
        (F.col("o_orderdate") >= F.to_date(F.lit(start_date)))
        & (F.col("o_orderdate") <= F.to_date(F.lit(end_date)))
        & (F.col("p_type") == p_type)
    )


def o_year(o_orderdate: pd.Series) -> htypes.column[pd.Series, int]:
    return pd.to_datetime(o_orderdate).dt.year


def volume(l_extendedprice: pd.Series, l_discount: pd.Series) -> htypes.column[pd.Series, float]:
    return l_extendedprice * (1 - l_discount)


def brazil_volume(n_name: pd.Series, volume: pd.Series) -> htypes.column[pd.Series, float]:
    return volume.where(n_name == "BRAZIL", 0)


@h_spark.with_columns(
    o_year,
    volume,
    brazil_volume,
    columns_to_pass=["o_orderdate", "l_extendedprice", "l_discount", "n_name", "volume"],
    select=["o_year", "volume", "brazil_volume"],
)
def processed(order_data_filtered: ps.DataFrame) -> ps.DataFrame:
    return order_data_filtered


def brazil_volume_by_year(processed: ps.DataFrame) -> ps.DataFrame:
    return processed.groupBy("o_year").agg(
        F.sum("volume").alias("sum_volume"), F.sum("brazil_volume").alias("sum_brazil_volume")
    )


def final_data(brazil_volume_by_year: ps.DataFrame) -> pd.DataFrame:
    return brazil_volume_by_year.toPandas()
