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
This script runs a Hamilton DAG whose intent is to create some features for input to a model.
The way the code is set up, is that you can do two things:

1. It uses Dask to parallelize computation. Use {"execution": "normal"} for this mode.
2. It uses Dask to parallelize computation and scale the data. It does this latter part by changing the way data
is loaded. Use {"execution": "dask"} for this mode. Note: the current validators implemented do not support dask
data types just yet.

The model fitting steps are not represented here, just the feature ingestion and transformation logic.

Use (1) if all your data can fit in memory, and you want to parallelize execution.
Use (2) if you need to scale to "big data" set sizes.

To run:
> python run_dask.py
"""

import logging
import sys

import data_loaders

# we need to tell hamilton where to load function definitions from
import feature_logic
from dask.distributed import Client, LocalCluster

from hamilton import base, driver
from hamilton.plugins import h_dask

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logger = logging.getLogger(__name__)
    # Setup a local cluster.
    # By default this sets up 1 worker per core
    cluster = LocalCluster()
    client = Client(cluster)
    logger.info(client.cluster)
    # passing in execution to help set up the right nodes for the DAG
    config = {"location": "Absenteeism_at_work.csv", "execution": "dask"}
    dga = h_dask.DaskGraphAdapter(client, base.PandasDataFrameResult())
    dr = driver.Driver(
        config, data_loaders, feature_logic, adapter=dga
    )  # can pass in multiple modules
    # we need to specify what we want in the final dataframe.
    output_columns = [
        "age",
        "age_zero_mean_unit_variance",
        "has_children",
        "is_summer",
        "has_pet",
        "day_of_the_week_2",
        "day_of_the_week_3",
        "day_of_the_week_4",
        "day_of_the_week_5",
        "day_of_the_week_6",
        "seasons_1",
        "seasons_2",
        "seasons_3",
        "seasons_4",
        "absenteeism_time_in_hours",
    ]
    # To visualize do `pip install "sf-hamilton[visualization]"` if you want these to work
    # dr.visualize_execution(output_columns, './run_dask', {"format": "png"})
    # dr.display_all_functions('./my_full_dag.dot')

    # let's create the dataframe!
    df = dr.execute(output_columns)
    print(df.head().to_string())
