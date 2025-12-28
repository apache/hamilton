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

import digit_loader
import iris_loader
import my_train_evaluate_logic

from hamilton import base, driver


def get_data_loader(data_set: str):
    """Returns the module to load that will procur data -- the data loaders all have to define the same functions."""
    if data_set == "iris":
        return iris_loader
    elif data_set == "digits":
        return digit_loader
    else:
        raise ValueError(f"Unknown data_name {data_set}.")


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
    # augment config
    dag_config.update(get_model_config(_model_type))
    # get module with functions to load data
    data_module = get_data_loader(_data_set)
    # set the desired result container we want
    adapter = base.DefaultAdapter()
    """
    What's cool about this, is that by simply changing the `dag_config` and the `data_module` we can
    reuse the logic in the `my_train_evaluate_logic` module very easily for different contexts and purposes if
    want to setup a generic model fitting and prediction dataflow!
    E.g. if we want to support a new data set, then we just need to add a new data loading module.
    E.g. if we want to support a new model type, then we just need to add a single conditional function
         to my_train_evaluate_logic.
    """
    dr = driver.Driver(dag_config, data_module, my_train_evaluate_logic, adapter=adapter)
    # ensure you have done "pip install "sf-hamilton[visualization]"" for the following to work:
    # dr.visualize_execution(['classification_report', 'confusion_matrix', 'fit_clf'],
    #                        f'./model_dag_{_data_set}_{_model_type}.dot', {"format": "png"})
    results = dr.execute(["classification_report", "confusion_matrix", "fit_clf"])
    for k, v in results.items():
        print(k, ":\n", v)
