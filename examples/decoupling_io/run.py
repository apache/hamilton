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

# Since this is not in plugins we need to import it *before* doing anything else
import importlib
from typing import List, Union

import click

importlib.import_module("adapters")

from components import feature_data, model_evaluation, model_training

from hamilton import base, driver
from hamilton.function_modifiers import source
from hamilton.io.materialization import ExtractorFactory, MaterializerFactory, from_, to


@click.group()
def cli():
    pass


modules = {
    "features_processed": [feature_data],
    "model_trained": [feature_data, model_training],
    "metrics_captured": [feature_data, model_training, model_evaluation],
}


def get_materializers(which_stage: str) -> List[Union[MaterializerFactory, ExtractorFactory]]:
    """Gives the set of materializers for the driver to run, separated out by stages.
    This demonstrates the evolution of additional materializers by stage, so that you can run
    stages individually using the same driver.

    :param which_stage: Stage to run
    :return: A list of materializers
    """

    # This represents the basic metrics_captured stage
    materializers = [
        from_.csv(path=source("location"), target="titanic_data"),
        to.pickle(
            id="save_trained_model", dependencies=["trained_model"], path="./model_saved.pickle"
        ),
        to.csv(
            id="save_training_data",
            dependencies=["train_set"],
            combine=base.PandasDataFrameResult(),
            path="./training_data.csv",
        ),
        to.png(
            id="save_confusion_matrix_plot",
            dependencies=["confusion_matrix_test_plot"],
            path="./confusion_matrix_plot.png",
        ),
    ]
    if which_stage == "features_processed":
        materializers = [materializers[0], materializers[2]]
    elif which_stage == "model_trained":
        materializers = materializers[0:3]
    return materializers


@cli.command()
@click.option(
    "--which-stage",
    type=click.Choice(["features_processed", "model_trained", "metrics_captured"]),
    required=True,
)
def run(which_stage: str):
    dr = driver.Driver({}, *modules[which_stage])
    materializers = get_materializers(which_stage)
    out = dr.materialize(
        *materializers,
        inputs={"location": "./data/titanic.csv", "test_size": 0.2, "random_state": 42},
    )
    print(out)


@cli.command()
@click.option(
    "--which-stage",
    type=click.Choice(["features_processed", "model_trained", "metrics_captured"]),
    required=True,
)
def visualize(which_stage: str):
    dr = driver.Driver({}, *modules[which_stage])
    materializers = get_materializers(which_stage)
    dr.visualize_materialization(
        *materializers,
        inputs={"location": "./data/titanic.csv", "test_size": 0.2, "random_state": 42},
        output_file_path=f"./{which_stage}",
    )


if __name__ == "__main__":
    cli()
