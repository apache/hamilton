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
from components import feature_transforms, iris_loader, models

from hamilton import driver as h_driver
from hamilton.io.materialization import to
from hamilton.lifecycle import PrintLnHook
from hamilton_sdk import adapters


@click.command()
@click.option(
    "--load-from-parquet", is_flag=True, help="Load from saved parquet or load fresh dataset."
)
@click.option("--username", help="Email for the Hamilton UI", type=str, required=True)
@click.option(
    "--project-id", help="Project ID to log to for the Hamilton UI", type=int, required=True
)
def run(load_from_parquet: bool, username: str, project_id: int):
    """
    Runs the machine_learning hamilton DAG emitting metadata to the Hamilton UI.

    Prerequisite - you need to have the Hamilton UI running:

    cd hamilton/ui/deployment  # directory with docker files

    ./run.sh  # will start docker

    """
    if load_from_parquet:
        config = {"case": "parquet"}
    else:
        config = {"case": "api"}
    dag_name = "machine_learning_dag"

    # create tracker object
    tracker = adapters.HamiltonTracker(
        username=username,
        project_id=project_id,
        dag_name=dag_name,
        tags={
            "template": "machine_learning",
            "loading_data_from": "parquet" if load_from_parquet else "api",
            "TODO": "add_more_tags_to_find_your_run_later",
            "custom_tag": "adding custom tag",
        },
    )

    # create driver object
    dr = (
        h_driver.Builder()
        .with_config(config)  # this shapes the DAG
        .with_modules(iris_loader, feature_transforms, models)
        .with_adapters(tracker, PrintLnHook(verbosity=1))
        .build()
    )
    inputs = {}
    # execute the DAG and materialize a few things from it
    metadata, result = dr.materialize(
        # This approach helps centralize & standardize how objects are read/written and also how metadata
        # about them is captured. This is useful for tracking lineage and provenance.
        to.parquet(
            id="data_set_v1_saver",
            path="data_set_v1.parquet",
            dependencies=["data_set_v1"],
        ),
        to.pickle(
            id="svm_model_saver",
            path="svm_model.pkl",
            dependencies=["svm_model"],
        ),
        to.pickle(
            id="lr_model_saver",
            path="lr_model.pkl",
            dependencies=["lr_model"],
        ),
        additional_vars=["best_model"],
        inputs=inputs,
    )
    print(metadata)  # metadata from the materialized artifacts
    print(result)  # contains result of the best model


if __name__ == "__main__":
    # import logging
    # logging.basicConfig(level=logging.DEBUG)
    run()
