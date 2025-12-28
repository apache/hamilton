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

"""This file shows different usage pattern to integrate Hamilton with Apache Airflow

For the purpose of this example, we will read and write data from the Airflow
installation location (${AIRFLOW_HOME}/plugins/data).
ref: https://docs.astronomer.io/learn/airflow-passing-data-between-tasks
"""

import os
from datetime import datetime

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context

AIRFLOW_HOME = os.getenv("AIRFLOW_HOME")

DEFAULT_DAG_PARAMS = dict(
    team="payment",
    hamilton_config=dict(
        raw_data_path="/some/path/to/file.parquet",
        season="summer",
    ),
)


@dag(
    dag_id="hamilton-how-to",
    description="Showcase different Hamilton usage pattern",
    start_date=datetime(2023, 6, 18),
    params=DEFAULT_DAG_PARAMS,
)
def hamilton_how_to_dag():
    @task
    def basic():
        """This is the simplest Hamilton usage pattern. Data is loaded from an external
        source. Then, it's properly formatted to pass it to hamilton.driver.execute().
        The execution results can be handled freely.

        0. import function modules
        1. load data from external source
        2. instantiate driver
        3. prepare inputs for driver
        4. execute driver
        5. handle results
        """
        import pandas as pd

        # 0. import function modules
        # feature_logic contains the data transformations;
        # find the file at hamilton/examples/airflow/plugins/functions_module/
        from function_modules import data_loaders, feature_logic

        from hamilton import driver

        # 1. load data from external source
        raw_df = pd.read_csv(f"{AIRFLOW_HOME}/plugins/data/Absenteeism_at_work.csv", sep=";")

        # 2. instantiate driver
        # the Python module `feature_logic` is passed to the driver
        dr = driver.Driver({}, feature_logic)

        # 3. prepare inputs for driver
        # hamilton.driver.execute() receives an an argument `inputs`, which is a dictionary
        # the keys should match the functions' arguments from the feature modules
        raw_df.columns = data_loaders._sanitize_columns(raw_df.columns)
        inputs = raw_df.to_dict(orient="series")

        final_vars = [
            "age_mean",
            "day_of_the_week_2",
            "day_of_the_week_3",
            "day_of_the_week_4",
            "day_of_the_week_5",
            "has_pet",
            "is_summer",
        ]

        # 4. execute driver
        results = dr.execute(final_vars=final_vars, inputs=inputs)

        # 5. handle results
        # print to airflow logs
        print(results.head())

    @task
    def data_loaders_and_savers():
        """Data is loaded using Hamilton's own data loading features. At execution,
        functions decorated with @load_from.* will load the specified source and take it
        as their node input. Similarly, the @save_to.* decorators will save the node
        output to the specified location. The @config.* decorators can be added to
        implement different behavior based on config (e.g., dev vs. prod).

        It is possible to combine this pattern with directy data loading in Airflow.

        0. import function and data loading modules
        1. define config
        2. instantiate driver
        3. execute driver
        4. handle results
        """
        # 0. import function modules
        # data_loaders defines data loading behavior
        # find the file at hamilton/examples/airflow/plugins/functions_module/
        from function_modules import data_loaders, feature_logic

        from hamilton import driver

        # 1. define config
        # define the driver config with the key `location` and the value poiting to the csv
        # data source. This will be read as `path` value of the `@load_from.csv()` decorator
        # of `raw_data__base()` found in `data_loaders.py`
        config = {"location": f"{AIRFLOW_HOME}/plugins/data/Absenteeism_at_work.csv"}

        # 2. instantiate driver
        # both Python module `feature_logic` and `data_loaders` are passed to driver
        dr = driver.Driver(config, feature_logic, data_loaders)

        # 3. execute driver
        final_vars = [
            "age_mean",
            "day_of_the_week_2",
            "day_of_the_week_3",
            "day_of_the_week_4",
            "day_of_the_week_5",
            "has_pet",
            "is_summer",
        ]

        results = dr.execute(final_vars=final_vars)

        # 4. save results
        # print to airflow logs
        print(results.head())

    @task
    def config_from_airflow_dag_file(hamilton_config: dict):
        """Load config from the @dag(params=) argument defined at the top of the file.
        The task receives `hamilton_config` from the passed Jinja2 string template
        """
        from function_modules import feature_logic

        from hamilton import driver

        # print to airflow logs
        print("config type: ", type(hamilton_config))
        print("config content: ", hamilton_config)

        dr = driver.Driver(hamilton_config, feature_logic)  # noqa: F841
        ...

    @task
    def config_from_airflow_runtime():
        """`get_current_context()` retrieves the runtime configuration of the airflow
        node. The nested object `hamilton_config` can then be retrieved.
        """
        from function_modules import feature_logic

        from hamilton import driver

        context = get_current_context()
        PARAMS = context["params"]
        hamilton_config = PARAMS.get("hamilton_config")

        # print to airflow logs
        print("config type: ", type(hamilton_config))
        print("config content: ", hamilton_config)

        dr = driver.Driver(hamilton_config, feature_logic)  # noqa: F841
        ...

    (
        basic()
        >> data_loaders_and_savers()
        # Get DAG params nested object using Jinja2 templated strings
        >> config_from_airflow_dag_file("{{params.hamilton_config}}")
        >> config_from_airflow_runtime()
    )


hamilton_how_to = hamilton_how_to_dag()
