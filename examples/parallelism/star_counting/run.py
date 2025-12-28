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
from typing import Tuple

import click
import functions

from hamilton import driver
from hamilton.execution import executors
from hamilton.log_setup import setup_logging

setup_logging(logging.INFO)


def _get_executor(mode: str):
    shutdown = None
    if mode == "local":
        remote_executor = executors.SynchronousLocalTaskExecutor()
    elif mode == "multithreading":
        remote_executor = executors.MultiThreadingExecutor(max_tasks=10)
    elif mode == "dask":
        from dask import distributed

        from hamilton.plugins import h_dask

        cluster = distributed.LocalCluster()
        client = distributed.Client(cluster)
        remote_executor = h_dask.DaskExecutor(client=client)
        shutdown = cluster.close
    else:
        import ray

        from hamilton.plugins import h_ray

        remote_executor = h_ray.RayTaskExecutor(num_cpus=4)
        shutdown = ray.shutdown
    return remote_executor, shutdown


@click.command()
@click.option(
    "--github-api-key",
    "-k",
    type=str,
    required=True,
    help="Github API key -- use from a secure storage location!.",
)
@click.option(
    "--repositories",
    "-r",
    multiple=True,
    help="Repositories to query from. Must be in pattern org/repository",
)
@click.option(
    "--mode",
    type=click.Choice(["local", "multithreading", "dask", "ray"]),
    default="multithreading",
    required=False,
    help="Where to run remote tasks.",
)
def main(github_api_key: str, repositories: Tuple[str, ...], mode: str):
    remote_executor, shutdown = _get_executor(mode)
    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_modules(functions)
        .with_remote_executor(remote_executor)
        .build()
    )

    # dr.visualize_execution(
    #     ['final_count'], "./dag", {}, inputs={
    #         'github_api_key': github_api_key,
    #         'repositories': list(repositories)})
    print(
        dr.execute(
            ["final_count", "unique_stargazers"],
            inputs={"github_api_key": github_api_key, "repositories": list(repositories)},
        )
    )
    if shutdown is not None:
        shutdown()


if __name__ == "__main__":
    main()
