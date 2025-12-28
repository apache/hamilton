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
from column_features import darkshore_flag, durotar_flag
from pyspark.sql import functions as sf

from hamilton.function_modifiers import schema
from hamilton.plugins.h_spark import with_columns

WORLD_OF_WARCRAFT_SCHEMA = (("zone", "str"), ("level", "int"), ("avatarId", "int"))


def spark_session() -> ps.SparkSession:
    return ps.SparkSession.builder.master("local[1]").getOrCreate()


@schema.output(*WORLD_OF_WARCRAFT_SCHEMA)
def world_of_warcraft(spark_session: ps.SparkSession) -> ps.DataFrame:
    return spark_session.read.parquet("data/wow.parquet")


@with_columns(darkshore_flag, durotar_flag, columns_to_pass=["zone"])
@schema.output(*WORLD_OF_WARCRAFT_SCHEMA, ("darkshore_flag", "int"), ("durotar_flag", "int"))
def with_flags(world_of_warcraft: ps.DataFrame) -> ps.DataFrame:
    return world_of_warcraft


@schema.output(("total_count", "int"), ("darkshore_count", "int"), ("durotar_count", "int"))
def zone_counts(with_flags: ps.DataFrame, aggregation_level: str) -> ps.DataFrame:
    return with_flags.groupby(aggregation_level).agg(
        sf.count("*").alias("total_count"),
        sf.sum("darkshore_flag").alias("darkshore_count"),
        sf.sum("durotar_flag").alias("durotar_count"),
    )


@schema.output(("mean_level", "float"))
def level_info(world_of_warcraft: ps.DataFrame, aggregation_level: str) -> ps.DataFrame:
    return world_of_warcraft.groupby(aggregation_level).agg(
        sf.mean("level").alias("mean_level"),
    )
