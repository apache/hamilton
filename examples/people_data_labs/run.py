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

import analysis

from hamilton import driver


def main():
    hamilton_driver = driver.Builder().with_modules(analysis).build()
    hamilton_driver.display_all_functions("all_functions.png", orient="TB")

    inputs = dict(
        pdl_file="pdl_data.json",
        stock_file="stock_data.json",
        rounds_selection=["series_a", "series_b", "series_c", "series_d"],
    )

    final_vars = [
        "n_company_by_funding_stage",
        "augmented_company_info",
    ]

    results = hamilton_driver.execute(final_vars, inputs=inputs)
    print(f"Successfully computed the nodes: {list(results.keys())}")
    print(results["augmented_company_info"].head())

    # add code to store results
    # ref: https://hamilton.apache.org/concepts/materialization/


if __name__ == "__main__":
    main()
