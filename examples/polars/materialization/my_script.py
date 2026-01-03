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

import logging
import sys

import polars as pl

from hamilton import driver
from hamilton.io.materialization import to
from hamilton.plugins import h_polars

# Add the hamilton module to your path - optinal before hamilton import
# project_dir = "### ADD PATH HERE ###"
# sys.path.append(project_dir)


logging.basicConfig(stream=sys.stdout)
initial_columns = {  # load from actuals or wherever -- this is our initial data we use as input.
    # Note: these values don't have to be all series, they could be a scalar.
    "signups": pl.Series([1, 10, 50, 100, 200, 400]),
    "spend": pl.Series([10, 10, 20, 40, 40, 50]),
}
# we need to tell hamilton where to load function definitions from
# programmatic code to load modules:
# module_name = "my_functions"
# my_functions = importlib.import_module(module_name)
# or import module(s) directly:

import my_functions

df_builder = h_polars.PolarsDataFrameResult()

dr = driver.Driver({}, my_functions)  # can pass in multiple modules
# we need to specify what we want in the final dataframe. These can be string names, or function references.
output_columns = [
    "spend",
    "signups",
    "avg_3wk_spend",
    "spend_per_signup",
    "spend_zero_mean_unit_variance",
]


materializers = [
    # materialize the dataframe to a parquet file
    to.parquet(
        dependencies=output_columns,
        id="df_to_parquet",
        file="./df.parquet",
        combine=df_builder,
    ),
    # materialize the dataframe to a feather file
    to.feather(
        dependencies=output_columns,
        id="df_to_feather",
        file="./df.feather",
        combine=df_builder,
    ),
    # materialize the dataframe to a json file
    to.json(
        dependencies=output_columns,
        id="df_to_json",
        file="./df.json",
        combine=df_builder,
    ),
    # materialize the dataframe to an ndjson file
    to.ndjson(
        dependencies=output_columns,
        id="df_to_ndjson",
        file="./df.ndjson",
        combine=df_builder,
    ),
    to.avro(
        dependencies=output_columns,
        id="df_to_avro",
        file="./df.avro",
        combine=df_builder,
    ),
    # materialize the dataframe to a spreadsheet file
    to.spreadsheet(
        dependencies=output_columns,
        id="df_to_spreadsheet",
        workbook="./df.xlsx",
        worksheet="Sheet1",
        combine=df_builder,
    ),
    # materialize the dataframe to a database
    to.database(
        dependencies=output_columns,
        id="df_to_database",
        table_name="test",
        connection="sqlite:///df.db",
        if_table_exists="replace",
        combine=df_builder,
    ),
]
# Visualize what is happening
dr.visualize_materialization(
    *materializers,
    additional_vars=output_columns,
    output_file_path="./dag",
    render_kwargs={"format": "png"},
    inputs=initial_columns,
)
# Materialize a result, i.e. execute the DAG!
materialization_results, additional_outputs = dr.materialize(
    *materializers,
    additional_vars=[
        "df_to_parquet_build_result",
        "df_to_feather_build_result",
        "df_to_json_build_result",
        "df_to_ndjson_build_result",
        "df_to_avro_build_result",
        "df_to_spreadsheet_build_result",
        "df_to_database_build_result",
    ],  # because combine is used, we can get that result here.
    inputs=initial_columns,
)
print(materialization_results)
print(additional_outputs["df_to_parquet_build_result"])
print(additional_outputs["df_to_feather_build_result"])
print(additional_outputs["df_to_json_build_result"])
print(additional_outputs["df_to_ndjson_build_result"])
print(additional_outputs["df_to_avro_build_result"])
print(additional_outputs["df_to_spreadsheet_build_result"])
print(additional_outputs["df_to_database_build_result"])
