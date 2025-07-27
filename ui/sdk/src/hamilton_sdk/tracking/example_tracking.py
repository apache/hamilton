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
import os
import sys
from types import ModuleType
from typing import Any, Dict, List

import click
import dagworks.driver
import pandas as pd

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

"""
Some basic examples
These are meant to be run from within the hamilton repo --
they use the examples there.
"""


def run_and_track(
    modules: List[ModuleType],
    inputs: Dict[str, Any],
    config: Dict[str, Any],
    project: int,
    username: str,
    api_key: str,
    output_vars: List[str] = None,
):
    """Run a hamilton driver and profiles to a file."""
    dr = dagworks.driver.Driver(
        config,
        *modules,
        adapter=None,
        api_key=api_key,
        username=username,
        project_id=project,
        dag_name="run_and_track_unit_test",
    )
    final_vars = (
        output_vars
        if output_vars is not None
        else [var.name for var in dr.list_available_variables()]
    )
    dr.initialize()
    dr.execute(final_vars=final_vars, inputs=inputs)


@click.group()
@click.option("--username", required=True, type=str)
@click.option("--api-key", required=True, type=str)
@click.pass_context
def run(ctx, username: str, api_key: str):
    ctx.ensure_object(dict)
    ctx.obj["username"] = username
    ctx.obj["api_key"] = api_key


# All of these are meant to be run from within the hamilton/examples directory
@run.command()
@click.pass_context
def run_hello_world(ctx):
    from examples.hello_world import my_functions

    inputs = {"spend": pd.Series([1, 2, 3, 4, 5]), "signups": pd.Series([1, 2, 3, 4, 5])}
    config = {}
    run_and_track(
        [my_functions],
        inputs=inputs,
        config=config,
        project=1,
        username=ctx.obj["username"],
        api_key=ctx.obj["api_key"],
    )


@run.command()
@click.pass_context
def run_data_quality(ctx):
    from data_quality.simple import data_loaders, feature_logic

    inputs = {}
    config = {"location": "data_quality/simple/Absenteeism_at_work.csv", "execution": "normal"}
    output_columns = [
        "age",
        "age_zero_mean_unit_variance",
        "has_children",
        "is_summer",
        "has_pet",
        "day_of_the_week_2",
        "day_of_the_week_3",
        "day_of_the_week_4",
        "day_of_the_week_5",
        "day_of_the_week_6",
        "seasons_1",
        "seasons_2",
        "seasons_3",
        "seasons_4",
        "absenteeism_time_in_hours",
    ]
    run_and_track(
        [data_loaders, feature_logic],
        inputs=inputs,
        config=config,
        project=2,
        username=ctx.obj["username"],
        api_key=ctx.obj["api_key"],
        output_vars=output_columns,
    )


@run.command()
@click.pass_context
def run_kaggle_competition_m5(ctx):
    # Run this from within the time_series
    import data_loaders
    import model_pipeline
    import transforms

    model_params = {
        "num_leaves": 555,
        "min_child_weight": 0.034,
        "feature_fraction": 0.379,
        "bagging_fraction": 0.418,
        "min_data_in_leaf": 106,
        "objective": "regression",
        "max_depth": -1,
        "learning_rate": 0.005,
        "boosting_type": "gbdt",
        "bagging_seed": 11,
        "metric": "rmse",
        "verbosity": -1,
        "reg_alpha": 0.3899,
        "reg_lambda": 0.648,
        "random_state": 222,
    }

    config = {
        "early_stopping_rounds": 2,
        "calendar_path": "m5-forecasting-accuracy/calendar.csv",
        "sell_prices_path": "m5-forecasting-accuracy/sell_prices.csv",
        "sales_train_validation_path": "m5-forecasting-accuracy/sales_train_validation.csv",
        "submission_path": "m5-forecasting-accuracy/sample_submission.csv",
        "load_test2": "False",
        "n_fold": 2,
        "model_params": model_params,
        "num_rows_to_skip": 27500000,  # for training set
    }

    inputs = {}
    output_vars = ["kaggle_submission_df"]
    run_and_track(
        [data_loaders, transforms, model_pipeline],
        inputs=inputs,
        config=config,
        project=3,
        username=ctx.obj["username"],
        api_key=ctx.obj["api_key"],
        output_vars=output_vars,
    )


@run.command()
@click.pass_context
def run_ad_hoc_api_calls(ctx):
    from hamilton_sdk.api.api_client import AuthenticatedClient

    client = AuthenticatedClient(
        os.environ.get("DAGWORKS_API_URL", "https://api.app.dagworks.io"),
        token=ctx.obj["api_key"],
        prefix="",
        auth_header_name="x-api-key",
        timeout=20.0,
        verify_ssl=True,
        raise_on_unexpected_status=True,
        headers={"x-api-user": f"{ctx.obj['username']}"},
    )
    from hamilton_sdk.api.api_client.api.auth.trackingserver_api_api_get_api_keys import sync

    sync(client=client)
    import pdb

    pdb.set_trace()
    # print(sync(project_id=1, client=client))


if __name__ == "__main__":
    run()
