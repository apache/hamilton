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

"""This is an example project using Hamilton with Apache Airflow

For the purpose of this example, we will read and write data from the Airflow
installation location (${AIRFLOW_HOME}/plugins/data).
For production environment, use intermediary storage.
ref: https://docs.astronomer.io/learn/airflow-passing-data-between-tasks
"""

import os
from datetime import datetime

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context

AIRFLOW_HOME = os.getenv("AIRFLOW_HOME")


"""Within the DAG config `DEFAULT_DAG_PARAMS`, the dictionaries `h_prepare_data` and
`h_train_and_evaluate_model` are configs that we will be passed to the Hamilton driver
of Airflow task `prepare_data` and `train_and_evaluate_model` respectively. The settings
`feature_set` and `label` are kept outside driver configs since they need to be
consistent across Airflow tasks.

The top-level config keys (`raw_data_location`, `feature_set`, etc.) are individual
input box in the Airflow UI, making them easy to edit manually. Therefore, you should
avoid nested objects. Your configuration should be limited to values that you will need
to change on the fly.
"""
DEFAULT_DAG_PARAMS = dict(
    raw_data_location=f"{AIRFLOW_HOME}/plugins/data/raw/Absenteeism_at_work.csv",
    feature_set=[
        "age_zero_mean_unit_variance",
        "has_children",
        "has_pet",
        "is_summer",
        "service_time",
    ],
    label="absenteeism_time_in_hours",
    validation_user_ids=[
        "1",
        "2",
        "4",
        "15",
        "17",
        "24",
        "36",
    ],
    h_prepare_data=dict(
        development_flag=True,
    ),
    h_train_and_evaluate_model=dict(
        development_flag=True,
        task="binary_classification",
        pred_path=f"{AIRFLOW_HOME}/plugins/data/results/val_predictions.csv",
        model_config={},
        scorer_name="accuracy",
        bootstrap_iter=1000,
    ),
)


@dag(
    dag_id="hamilton-absenteeism-prediction",
    description="Predict absenteeism using Hamilton and Airflow",
    start_date=datetime(2023, 6, 18),
    params=DEFAULT_DAG_PARAMS,
)
def absenteeism_prediction_dag():
    """Predict absenteeism using Hamilton and Airflow

    The workflow is composed of 2 tasks, each with its own Hamilton driver.
    Notice that the task `prepare_data` relies on the Python module `prepare_data.py`,
    while the task `train_and_evaluate_model` relies on two Python modules
    `train_model.py` and `evaluate_model.py`. Each Python module describes related sets
    of functions, but in the context of this Airflow DAG it made sense to run the
    model training and evaluation in the same node!
    """

    @task
    def prepare_data():
        """Load external data, preprocess dataset, and store cleaned data"""
        # Python imports
        import pandas as pd

        # function modules imports from airflow/plugins directory
        from absenteeism import prepare_data

        from hamilton import driver

        # load DAG params
        context = get_current_context()
        PARAMS = context["params"]

        # load external data; could be data from S3, Snowflake, BigQuery, etc.
        raw_data_location = PARAMS["raw_data_location"]
        raw_df = pd.read_csv(raw_data_location, sep=";")

        # instantiate Hamilton driver
        hamilton_config = PARAMS["h_prepare_data"]
        dr = driver.Driver(hamilton_config, prepare_data)

        # execute Hamilton driver
        label = PARAMS["label"]
        # prepare_data.ALL_FEATURES is a constant defined in the module
        features_df = dr.execute(
            final_vars=prepare_data.ALL_FEATURES + [label],
            inputs={"raw_df": raw_df},
        )

        # save preprocessed directory for multiple reused
        features_path = f"{AIRFLOW_HOME}/plugins/data/features/full_feature_set.parquet"
        features_df.to_parquet(features_path)

        # `return` pushes to Airflow XCom a string path
        return features_path

    @task
    def train_and_evaluate_model(features_path: str):
        """Train and evaluate a machine learning model"""
        from absenteeism import evaluate_model, train_model

        from hamilton import base, driver

        context = get_current_context()
        PARAMS = context["params"]

        hamilton_config = PARAMS["h_train_and_evaluate_model"]
        dr = driver.Driver(
            hamilton_config,
            train_model,
            evaluate_model,  # pass two function module to the Hamilton driver
            adapter=base.DefaultAdapter(),
        )

        results = dr.execute(
            final_vars=["save_validation_preds", "model_results"],
            inputs={
                "features_path": features_path,  # value retrieved from Airflow XCom
                "label": PARAMS["label"],
                "feature_set": PARAMS["feature_set"],
                "validation_user_ids": PARAMS["validation_user_ids"],
            },
        )

        print(results)

    (train_and_evaluate_model(prepare_data()))


absenteeism_prediction = absenteeism_prediction_dag()
