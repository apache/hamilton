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

import store_definitions
import store_operations

from hamilton import base, driver


def main():
    dr = driver.Driver(
        dict(feast_repository_path=".", feast_config={}),
        store_operations,
        store_definitions,
        adapter=base.SimplePythonGraphAdapter(base.DictResult()),
    )

    final_vars = [
        "apply",
        "registry_diff",
    ]

    inputs = dict(
        trips_stats_3h_path="./data/trips_stats_3h.parquet",
        driver_source_path="./data/driver_stats.parquet",
    )

    out = dr.execute(final_vars=final_vars, inputs=inputs)

    # uncomment these to display execution graph
    # dr.display_all_functions("definitions", {"format": "png"})
    # dr.visualize_execution(final_vars, "exec", {"format": "png"}, inputs=inputs)

    print(out.keys())


if __name__ == "__main__":
    main()
