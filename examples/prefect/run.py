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

import evaluate_model
import pandas as pd

# import modules containing your dataflow functions
import prepare_data
import train_model
from prefect import flow, task

from hamilton import base, driver


# use the @task to define Prefect tasks, which adds logging, retries, etc.
# the function parameters define the config and inputs needed by Hamilton
@task
def prepare_data_task(
    raw_data_location: str,
    hamilton_config: dict,
    label: str,
    results_dir: str,
) -> str:
    """Load external data, preprocess dataset, and store cleaned data"""
    raw_df = pd.read_csv(raw_data_location, sep=";")

    dr = driver.Driver(hamilton_config, prepare_data)

    # prepare_data.ALL_FEATURES is a constant defined in the module
    features_df = dr.execute(
        final_vars=prepare_data.ALL_FEATURES + [label],
        inputs={"raw_df": raw_df},
    )

    # save results to local file; for prod, save to an S3 bucket instead
    features_path = f"{results_dir}/features.csv"
    features_df.to_csv(features_path)

    return features_path


@task
def train_and_evaluate_model_task(
    features_path: str,
    hamilton_config: str,
    label: str,
    feature_set: list[str],
    validation_user_ids: list[str],
) -> None:
    """Train and evaluate machine learning model"""
    dr = driver.Driver(
        hamilton_config,
        train_model,
        evaluate_model,
        adapter=base.SimplePythonGraphAdapter(base.DictResult()),
    )

    dr.execute(
        final_vars=["save_validation_preds", "model_results"],
        inputs=dict(
            features_path=features_path,
            label=label,
            feature_set=feature_set,
            validation_user_ids=validation_user_ids,
        ),
    )


# use @flow to define the Prefect flow.
# the function parameters define the config and inputs needed by all tasks
# this way, we prevent having constants being hardcoded in the flow or task body
@flow(
    name="hamilton-absenteeism-prediction",
    description="Predict absenteeism using Hamilton and Prefect",
)
def absenteeism_prediction_flow(
    raw_data_location: str = "./data/Absenteeism_at_work.csv",
    feature_set: list[str] = [  # noqa: B006
        "age_zero_mean_unit_variance",
        "has_children",
        "has_pet",
        "is_summer",
        "service_time",
    ],
    label: str = "absenteeism_time_in_hours",
    validation_user_ids: list[str] = [  # noqa: B006
        "1",
        "2",
        "4",
        "15",
        "17",
        "24",
        "36",
    ],
):
    """Predict absenteeism using Hamilton and Prefect

    The workflow is composed of 2 tasks, each with its own Hamilton driver.
    Notice that the task `prepare_data_task` relies on the Python module `prepare_data.py`,
    while the task `train_and_evaluate_model_task` relies on two Python modules
    `train_model.py` and `evaluate_model.py`.
    """

    # the task returns the string value `features_path`, by passing this value
    # to the next task, Prefect is able to generate the dependencies graph
    features_path = prepare_data_task(
        raw_data_location=raw_data_location,
        hamilton_config=dict(
            development_flag=True,
        ),
        label=label,
        results_dir="./data",
    )

    train_and_evaluate_model_task(
        features_path=features_path,
        hamilton_config=dict(
            development_flag=True,
            task="binary_classification",
            pred_path="./data/predictions.csv",
            model_config={},
            scorer_name="accuracy",
            bootstrap_iter=1000,
        ),
        label=label,
        feature_set=feature_set,
        validation_user_ids=validation_user_ids,
    )


if __name__ == "__main__":
    absenteeism_prediction_flow()
