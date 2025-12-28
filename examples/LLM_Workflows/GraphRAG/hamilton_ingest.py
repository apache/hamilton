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

import ingest_fighters
import ingest_fights
from falkordb import FalkorDB

from hamilton import driver
from hamilton.execution import executors


def main():
    # Connect to FalkorDB
    db = FalkorDB(host="localhost", port=6379)
    g = db.select_graph("UFC")

    # Clear previous graph
    if "UFC" in db.list_graphs():
        g.delete()

    # ---- load fighters ----

    # Note if you want to track the progress of the load you can use the Hamilton UI:
    # from hamilton_sdk import adapters
    # tracker = adapters.HamiltonTracker(
    #    project_id=44,  # modify this as needed
    #    username="elijah@dagworks.io",
    #    dag_name="load_fighters",
    #    tags={"environment": "DEV", "team": "MY_TEAM", "version": "X"}
    # )
    # build the hamilton Driver
    fighter_loader = (
        driver.Builder()
        .with_modules(ingest_fighters)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(executors.MultiThreadingExecutor(5))
        # .with_adapters(tracker)  # <-- uncomment this line if you want to track the progress
        .build()
    )
    # display the functions in the module
    fighter_loader.display_all_functions("ingest_fighters.png")
    fighter_results = fighter_loader.execute(["write_to_graph"], inputs={"graph": g})

    # ---- load fights ----

    # if you have the Hamilton UI you can see progress:
    # from hamilton_sdk import adapters
    # tracker = adapters.HamiltonTracker(
    #    project_id=44,  # modify this as needed
    #    username="elijah@dagworks.io",
    #    dag_name="load_fights",
    #    tags={"environment": "DEV", "team": "MY_TEAM", "version": "X"}
    # )
    fights_loader = (
        driver.Builder()
        .with_modules(ingest_fights)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(
            executors.MultiThreadingExecutor(5)
        )  # this will do 5 concurrent inserts
        # .with_adapters(tracker)  # <-- uncomment this line if you want to track the progress
        .build()
    )
    # display the functions in the module
    fights_loader.display_all_functions("ingest_fights.png")
    fight_results = fights_loader.execute(["collect_writes"], inputs={"graph": g})

    print(
        f"All done - loaded {fighter_results['write_to_graph']} fighters and {fight_results['collect_writes']} fights."
    )


if __name__ == "__main__":
    main()
