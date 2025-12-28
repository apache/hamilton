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
from math import ceil

import pandas as pd
import pytest
from kedro.io import DataCatalog
from kedro.runner import SequentialRunner
from kedro_code.pipelines.data_science import create_pipeline as create_ds_pipeline
from kedro_code.pipelines.data_science.nodes import split_data


@pytest.fixture
def dummy_data():
    return pd.DataFrame(
        {
            "engines": [1, 2, 3],
            "crew": [4, 5, 6],
            "passenger_capacity": [5, 6, 7],
            "price": [120, 290, 30],
        }
    )


@pytest.fixture
def dummy_parameters():
    parameters = {
        "model_options": {
            "test_size": 0.2,
            "random_state": 3,
            "features": ["engines", "passenger_capacity", "crew"],
        }
    }
    return parameters


def test_split_data(dummy_data, dummy_parameters):
    model_opts = dummy_parameters["model_options"]
    n_rows = dummy_data.shape[0]
    expected_test_size = ceil(model_opts["test_size"] * n_rows)
    expected_train_size = n_rows - expected_test_size

    X_train, X_test, y_train, y_test = split_data(dummy_data, model_opts)
    assert len(X_train) == expected_train_size
    assert len(y_train) == expected_train_size
    assert len(X_test) == expected_test_size
    assert len(y_test) == expected_test_size


def test_split_data_missing_price(dummy_data, dummy_parameters):
    dummy_data_missing_price = dummy_data.drop(columns="price")
    with pytest.raises(KeyError) as e_info:
        X_train, X_test, y_train, y_test = split_data(
            dummy_data_missing_price, dummy_parameters["model_options"]
        )

    assert "price" in str(e_info.value)


def test_data_science_pipeline(caplog, dummy_data, dummy_parameters):
    pipeline = (
        create_ds_pipeline()
        .from_nodes("split_data_node")
        .to_nodes("evaluate_model_node")
    )
    catalog = DataCatalog()
    catalog.add_feed_dict(
        {
            "model_input_table": dummy_data,
            "params:model_options": dummy_parameters["model_options"],
        }
    )

    caplog.set_level(logging.DEBUG, logger="kedro")
    successful_run_msg = "Pipeline execution completed successfully."

    SequentialRunner().run(pipeline, catalog)

    assert successful_run_msg in caplog.text
