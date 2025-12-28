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

import pandas as pd
import pytest

from hamilton import driver
from hamilton_code import data_science


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
def dummy_inputs():
    return {
        "test_size": 0.2,
        "random_state": 3,
        "features": ["engines", "passenger_capacity", "crew"],
    }


def test_split_data(dummy_data, dummy_inputs):
    results = data_science.split_data(create_model_input_table=dummy_data, **dummy_inputs)
    assert len(results["X_train"]) == 2
    assert len(results["y_train"]) == 2
    assert len(results["X_test"]) == 1
    assert len(results["y_test"]) == 1


def test_split_data_missing_price(dummy_data, dummy_inputs):
    dummy_data_missing_price = dummy_data.drop(columns="price")
    with pytest.raises(KeyError) as e_info:
        X_train, X_test, y_train, y_test = data_science.split_data(
            create_model_input_table=dummy_data_missing_price, **dummy_inputs
        )

    assert "price" in str(e_info.value)


def test_data_science_pipeline(dummy_data, dummy_inputs):
    dr = driver.Builder().with_modules(data_science).build()
    results = dr.execute(
        ["evaluate_model"],
        inputs=dict(
            create_model_input_table=dummy_data,
            **dummy_inputs,
        ),
    )

    assert results["evaluate_model"]
