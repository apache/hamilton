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

from typing import Iterable, Tuple

import click
import functions
import pandas as pd
from dask import distributed

from hamilton import driver
from hamilton.execution import executors
from hamilton.lifecycle import GracefulErrorAdapter
from hamilton.plugins import h_dask

# Assume we define some custom methods for splittings


def split_on_region(data: pd.DataFrame) -> Iterable[Tuple[str, pd.DataFrame]]:
    for idx, grp in data.groupby("Region"):
        yield f"Region:{idx}", grp


def split_on_attrs(data: pd.DataFrame) -> Iterable[Tuple[str, pd.DataFrame]]:
    for (region, method), grp in data.groupby(["Region", "Method"]):
        yield f"Region:{region} - Method:{method}", grp


def split_on_views(data: pd.DataFrame) -> Iterable[Tuple[str, pd.DataFrame]]:
    yield "Low Views", data[data.Views <= 4000.0]
    yield "High Views", data[data.Views > 4000.0]


@click.command()
@click.option(
    "--mode",
    type=click.Choice(["local", "multithreading", "dask"]),
    help="Where to run remote tasks.",
    default="local",
)
@click.option("--no-adapt", is_flag=True, default=False, help="Disable the graceful adapter.")
def main(mode: str, no_adapt: bool):
    adapter = GracefulErrorAdapter(
        error_to_catch=Exception,
        sentinel_value=None,
        try_all_parallel=True,
    )

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

    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(remote_executor)
        .with_modules(functions)
    )
    if not no_adapt:
        dr = dr.with_adapters(adapter)
    dr = dr.build()

    the_funcs = [split_on_region, split_on_attrs, split_on_views]
    dr.visualize_execution(
        ["final_collect"], "./dag", {}, inputs={"funcs": the_funcs}, show_legend=False
    )

    print(
        dr.execute(
            final_vars=["final_collect"],
            inputs={"funcs": the_funcs},
        )["final_collect"]
    )
    if shutdown:
        shutdown()


if __name__ == "__main__":
    main()
