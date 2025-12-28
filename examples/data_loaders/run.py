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

import click
import load_data_csv
import load_data_duckdb
import load_data_mock
import prep_data

import hamilton.driver


@click.group()
def main():
    pass


VARS = [
    "total_signups",
    "total_churn",
    "total_marketing_spend",
    "acquisition_cost",
    "twitter_spend_smoothed",
    "facebook_spend_smoothed",
    "radio_spend_smoothed",
    "tv_spend_smoothed",
    "billboards_spend_smoothed",
    "youtube_spend_smoothed",
]


@main.command()
def duckdb():
    driver = hamilton.driver.Driver(
        {"db_path": "./test_data/database.duckdb"}, load_data_duckdb, prep_data
    )
    print(driver.execute(VARS))
    # driver.visualize_execution(VARS, './duckdb_execution_graph', {"format": "png"})


@main.command()
def csv():
    driver = hamilton.driver.Driver({"db_path": "test_data"}, load_data_csv, prep_data)
    print(driver.execute(VARS))
    # driver.visualize_execution(VARS, "./csv_execution_graph", {"format": "png"})


@main.command()
def mock():
    driver = hamilton.driver.Driver({}, load_data_mock, prep_data)
    print(driver.execute(VARS))
    # driver.visualize_execution(VARS, './mock_execution_graph', {"format": "png"})


if __name__ == "__main__":
    main()
