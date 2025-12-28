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


def spark_session() -> ps.SparkSession:
    return ps.SparkSession.builder.master("local[1]").getOrCreate()


def world_of_warcraft(spark_session: ps.SparkSession) -> ps.DataFrame:
    return spark_session.read.parquet("data/wow.parquet")


def zone_flags(world_of_warcraft: ps.DataFrame) -> ps.DataFrame:
    zone_flags = world_of_warcraft
    zone_flags = zone_flags.withColumn(
        "darkshore_flag", sf.when(sf.col("zone") == " Darkshore", 1).otherwise(0)
    ).withColumn("durotar_flag", sf.when(sf.col("zone") == " Durotar", 1).otherwise(0))
    return zone_flags


def zone_counts(zone_flags: ps.DataFrame, aggregation_level: str) -> ps.DataFrame:
    return zone_flags.groupby(aggregation_level).agg(
        sf.count("*").alias("total_count"),
        sf.sum("darkshore_flag").alias("darkshore_count"),
        sf.sum("durotar_flag").alias("durotar_count"),
    )


def zone_likelihoods(zone_counts: ps.DataFrame) -> ps.DataFrame:
    zone_likelihoods = zone_counts
    for zone in ["durotar", "darkshore"]:
        zone_likelihoods = zone_likelihoods.withColumn(
            f"{zone}_likelihood", sf.col(f"{zone}_count") / sf.col("total_count")
        )
    return zone_likelihoods
