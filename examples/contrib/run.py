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

from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split

from hamilton import base, driver

# import the dataflow from the contrib module
from hamilton.contrib.user.zilto import xgboost_optuna
from hamilton.io.materialization import to
from hamilton.plugins import xgboost_extensions  # noqa: F401

if __name__ == "__main__":
    dr = (
        driver.Builder()
        .with_modules(xgboost_optuna)  # use the contrib dataflow
        .with_config(dict(task="classification"))
        .build()
    )

    # Load the Boston Housing dataset (regression example)
    data = load_breast_cancer()
    X_train, X_test, y_train, y_test = train_test_split(
        data.data, data.target, test_size=0.2, random_state=42
    )

    inputs = dict(
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
    )

    materializers = [
        to.json(
            dependencies=["best_model"],
            id="best_model_json",
            path="./data/best_model.json",
        ),
        to.json(
            dependencies=["best_hyperparameters"],
            id="best_hyperparameters_json",
            path="./data/best_hyperparameters.json",
        ),
        to.json(
            dependencies=["test_score"],
            id="results_json",
            path="./data/results.json",
            combine=base.DictResult(),
        ),
    ]

    dr.visualize_materialization(
        *materializers,
        output_file_path="./data/dag",
        render_kwargs=dict(format="png", view=False),
        inputs=inputs,
        deduplicate_inputs=True,
    )

    dr.materialize(
        *materializers,
        inputs=inputs,
    )
