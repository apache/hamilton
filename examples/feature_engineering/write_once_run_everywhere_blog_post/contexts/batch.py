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

import click
from components import aggregations, data_loaders, features, joins, model

from hamilton import driver


@click.group()
def cli():
    pass


def _create_driver() -> driver.Driver:
    return driver.Driver({"mode": "batch"}, aggregations, data_loaders, joins, features, model)


def _get_inputs() -> dict:
    return {
        "client_login_db": "login_data",
        "client_login_table": "client_logins",
        "survey_results_db": "survey_data",
        "survey_results_table": "survey_results",
        "execution_time": datetime.datetime.now(),
    }


@cli.command()
def run():
    """This command will run the ETL, and print it out to the terminal"""
    dr = _create_driver()
    df = dr.execute(["predictions"], inputs=_get_inputs())
    print(df)


@cli.command()
@click.option("--output-file", default="./out", help="Output file to write to")
def visualize(output_file: str):
    """This command will visualize execution"""
    dr = _create_driver()
    return dr.visualize_execution(
        ["predictions"], output_file, {"format": "png"}, inputs=_get_inputs()
    )


if __name__ == "__main__":
    cli()
