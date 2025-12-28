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

import pyspark.sql as ps
from pyspark.sql import functions as sf
from zone_features__common import (
    darkshore_flag,
    darkshore_likelihood,
    durotar_flag,
    durotar_likelihood,
)

from hamilton.plugins.h_spark import with_columns


def spark_session() -> ps.SparkSession:
    return ps.SparkSession.builder.master("local[1]").getOrCreate()


def world_of_warcraft(spark_session: ps.SparkSession) -> ps.DataFrame:
    return spark_session.read.parquet("data/wow.parquet")


@with_columns(darkshore_flag, durotar_flag, columns_to_pass=["zone"])
def with_flags(world_of_warcraft: ps.DataFrame, aggregation_level: str) -> ps.DataFrame:
    return world_of_warcraft


def zone_counts(with_flags: ps.DataFrame, aggregation_level: str) -> ps.DataFrame:
    return with_flags.groupby(aggregation_level).agg(
        sf.count("*").alias("total_count"),
        sf.sum("darkshore_flag").alias("darkshore_count"),
        sf.sum("durotar_flag").alias("durotar_count"),
    )


@with_columns(
    darkshore_likelihood,
    durotar_likelihood,
    columns_to_pass=["durotar_count", "darkshore_count", "total_count"],
)
def zone_likelihoods(zone_counts: ps.DataFrame) -> ps.DataFrame:
    return zone_counts
