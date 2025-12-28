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

import aggregate_data
import click
import list_data
import process_data
import ray
from dask import distributed

from hamilton import driver, log_setup
from hamilton.execution import executors
from hamilton.plugins import h_dask, h_ray

log_setup.setup_logging(logging.INFO)


@click.command()
@click.option(
    "--mode",
    type=click.Choice(["local", "multithreading", "dask", "ray"]),
    required=True,
    help="Where to run remote tasks.",
)
def main(mode: str):
    shutdown = None
    if mode == "local":
        remote_executor = executors.SynchronousLocalTaskExecutor()
    elif mode == "multithreading":
        remote_executor = executors.MultiThreadingExecutor(max_tasks=100)
    elif mode == "dask":
        cluster = distributed.LocalCluster()
        client = distributed.Client(cluster)
        remote_executor = h_dask.DaskExecutor(client=client)
        shutdown = cluster.close
    else:
        remote_executor = h_ray.RayTaskExecutor(num_cpus=4)
        shutdown = ray.shutdown
    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(remote_executor)  # We only need to specify remote exeecutor
        # The local executor just runs it synchronously
        .with_modules(aggregate_data, list_data, process_data)
        .build()
    )
    print(
        dr.execute(final_vars=["statistics_by_city"], inputs={"data_dir": "data"})[
            "statistics_by_city"
        ]
    )
    if shutdown:
        shutdown()


if __name__ == "__main__":
    main()
