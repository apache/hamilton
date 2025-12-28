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
from python_transforms import data_loader, feature_transforms, model_pipeline

from hamilton import base, driver


def model(dbt, session):
    """A DBT model that does a lot -- it's all delegated to the hamilton framework though.
    The goal of this is to show how DBT can work for SQL/orchestration, while Hamilton can
    work for workflow modeling (in both the micro/macro sense) and help integrate python in.

    :param dbt: DBT object to get refs/whatnot
    :param session: duckdb session info (as needed)
    :return: A dataframe containing predictions corresponding to the input data
    """
    raw_passengers_df = dbt.ref("raw_passengers")
    # Instantiate a simple graph adapter to get the base result
    adapter = base.DefaultAdapter()
    # DAG for training/inferring on titanic data
    titanic_dag = driver.Driver(
        {
            "random_state": 5,
            "test_size": 0.2,
            "model_to_use": "create_new",
        },
        data_loader,
        feature_transforms,
        model_pipeline,
        adapter=adapter,
    )
    # gather results
    results = titanic_dag.execute(
        final_vars=["model_predict"], inputs={"raw_passengers_df": raw_passengers_df}
    )
    # pip install "sf-hamilton[visualization]" to get this to work
    # titanic_dag.visualize_execution(["model_predict"], './titanic_dbt', {"format": "png"},
    #                                 inputs={"raw_passengers_df": raw_passengers_df})
    # Take the "predictions" result, which is an np array
    predictions = results["model_predict"]
    # Return a dataframe!
    return pd.DataFrame(predictions, columns=["prediction"])
