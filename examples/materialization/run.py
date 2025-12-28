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

"""
Example script showing how one might setup a generic model training pipeline that is quickly configurable.
"""

import importlib

# Required import to register adapters
import os

import data_loaders
import model_training

from hamilton import base, driver
from hamilton.io.materialization import to

# This has to be imported, but the linter doesn't like it cause its unused
# We just need to import it to register the materializers
importlib.import_module("custom_materializers")


def get_model_config(model_type: str) -> dict:
    """Returns model type specific configuration"""
    if model_type == "svm":
        return {"clf": "svm", "gamma": 0.001}
    elif model_type == "logistic":
        return {"clf": "logistic", "penalty": "l2"}
    else:
        raise ValueError(f"Unsupported model {model_type}.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Error: required arguments are [iris|digits] [svm|logistic]")
        sys.exit(1)
    _data_set = sys.argv[1]  # the data set to load
    _model_type = sys.argv[2]  # the model type to fit and evaluate with

    dag_config = {
        "test_size_fraction": 0.5,
        "shuffle_train_test_split": True,
    }
    if not os.path.exists("data"):
        os.mkdir("data")
    # augment config
    dag_config.update(get_model_config(_model_type))
    dag_config["data_loader"] = _data_set
    dr = (
        driver.Builder()
        .with_adapter(base.DefaultAdapter())
        .with_config(dag_config)
        .with_modules(data_loaders, model_training)
        .build()
    )
    materializers = [
        to.json(
            dependencies=["model_parameters"], id="model_params_to_json", path="./data/params.json"
        ),
        # classification report to .txt file
        to.file(
            dependencies=["classification_report"],
            id="classification_report_to_txt",
            path="./data/classification_report.txt",
        ),
        # materialize the model to a pickle file
        to.pickle(dependencies=["fit_clf"], id="clf_to_pickle", path="./data/clf.pkl"),
        # materialize the predictions we made to a csv file
        to.csv(
            dependencies=["predicted_output_with_labels"],
            id="predicted_output_with_labels_to_csv",
            path="./data/predicted_output_with_labels.csv",
        ),
    ]
    dr.visualize_materialization(
        *materializers,
        additional_vars=["classification_report"],
        output_file_path="./dag",
        render_kwargs={},
    )
    materialization_results, additional_vars = dr.materialize(
        # materialize model parameters to json
        *materializers,
        additional_vars=["classification_report"],
    )
    # print(materialization_results["classification_report"])
    # print(additional_vars)
