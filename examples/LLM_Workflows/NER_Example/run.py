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

import argparse

import lancedb_module
import ner_extraction

from hamilton import driver, lifecycle


def build_driver(adapter_list):
    """Builds the driver with the necessary modules and adapters."""
    dr = (
        driver.Builder()
        .with_config({})
        .with_modules(ner_extraction, lancedb_module)
        .with_adapters(*adapter_list)
        .build()
    )
    return dr


def load_data(table_name: str, use_tracker: bool = False):
    """Runs the DAG to load data into LanceDB."""
    adapter_list = [lifecycle.PrintLn()]
    if use_tracker:
        from hamilton_sdk import adapters

        tracker = adapters.HamiltonTracker(
            project_id=41,  # modify this as needed
            username="elijah@dagworks.io",  # modify this as needed
            dag_name="ner-lancedb-pipeline",
            tags={"context": "extraction", "team": "MY_TEAM", "version": "1"},
        )
        adapter_list.append(tracker)

    dr = build_driver(adapter_list)
    # display the graph
    dr.display_all_functions("ner_extraction_pipeline.png")

    results = dr.execute(
        ["load_into_lancedb"],
        inputs={"table_name": table_name},
    )
    print(results)


def query_data(query: str, table_name: str, use_tracker: bool = False):
    """Runs the DAG to query LanceDB."""
    adapter_list = [lifecycle.PrintLn()]
    if use_tracker:
        from hamilton_sdk import adapters

        tracker = adapters.HamiltonTracker(
            project_id=41,  # modify this as needed
            username="elijah@dagworks.io",  # modify this as needed
            dag_name="ner-lancedb-pipeline",
            tags={"context": "inference", "team": "MY_TEAM", "version": "1"},
        )
        adapter_list.append(tracker)

    dr = build_driver(adapter_list)

    r = dr.execute(["lancedb_result"], inputs={"query": query, "table_name": table_name})
    print(r)


if __name__ == "__main__":
    """
    Some example commands:
    > python run.py medium_docs load
    > python run.py medium_docs query --query "Why does SpaceX want to build a city on Mars?"
    > python run.py medium_docs query --query "How are autonomous vehicles changing the world?"
    """
    parser = argparse.ArgumentParser(description="Process command-line arguments.")
    parser.add_argument("table_name", help="The name of the table.")
    parser.add_argument("operation", choices=["load", "query"], help="The operation to perform.")
    parser.add_argument("--query", help="The query to run. Required if operation is 'query'.")
    parser.add_argument("--use-tracker", action="store_true", help="Whether to use the tracker.")

    args = parser.parse_args()

    if args.operation == "query" and args.query is None:
        parser.error("The --query argument is required when operation is 'query'.")

    if args.operation == "load":
        load_data(args.table_name, args.use_tracker)
    else:
        query_data(args.query, args.table_name, args.use_tracker)
