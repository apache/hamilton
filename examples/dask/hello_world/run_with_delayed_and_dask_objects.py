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

import importlib
import logging
import sys

from hamilton import driver
from hamilton.plugins import h_dask

logger = logging.getLogger(__name__)

"""
This example shows you how to run a Hamilton DAG and:
 - shoehorn loading data via a dask and reusing business logic in pandas
 - while also using dask.delayed to farm out computation (which is kind of nonsensical in this example)
 - and using the dask dataframe result builder to get back the final dataframe.
"""

if __name__ == "__main__":
    from dask.distributed import Client, LocalCluster

    # Setup a local cluster.
    # By default this sets up 1 worker per core
    cluster = LocalCluster()
    client = Client(cluster)
    logger.info(client.cluster)
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    # easily replace how data is loaded by replacing the data_loaders module
    module_names = ["business_logic", "data_loaders"]  # or just import the modules directly
    modules = [importlib.import_module(m) for m in module_names]
    dga = h_dask.DaskGraphAdapter(
        client,
        h_dask.DaskDataFrameResult(),
        visualize_kwargs={"filename": "run_with_delayed_with_dask_objects.png", "format": "png"},
        use_delayed=True,
        compute_at_end=True,
    )
    # will output Dask's execution graph  -- requires sf-hamilton[visualization] to be installed.
    initial_config_and_data = {
        "spend_location": "some file path",
        "spend_partitions": 2,
        "signups_location": "some file path",
        "signups_partitions": 2,
        "foobar": "some_other_data",
    }
    dr = driver.Driver(initial_config_and_data, *modules, adapter=dga)

    output_columns = [
        "spend",
        "signups",
        "avg_3wk_spend",
        "spend_per_signup",
        "spend_mean",
        "spend_zero_mean_unit_variance",
        "foobar",
    ]
    dask_df = dr.execute(output_columns)  # it's dask dataframe -- it hasn't been evaluated yet.
    logger.info(dask_df.to_string())  # this should be empty
    df = dask_df.compute()
    # To visualize do `pip install "sf-hamilton[visualization]"` if you want these to work
    # dr.visualize_execution(output_columns, './hello_world_dask', {"format": "png"})
    # dr.display_all_functions('./my_full_dag.dot')
    logger.info(df.to_string())
    client.shutdown()
