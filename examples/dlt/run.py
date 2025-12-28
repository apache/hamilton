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

import os

import dlt
import slack
import transform

from hamilton import driver


def main(
    selected_channels: list[str],
    ingestion_full_refresh: bool = False,
):
    """ELT pipeline to load Slack messages and replies,
    then reassemble threads and use an LLM to summarize it.

    dlt does "Extract, Load"; Hamilton does "Transform"
    """

    # dlt
    slack_pipeline = dlt.pipeline(
        pipeline_name="slack",
        destination="duckdb",
        dataset_name="slack_data",
        full_refresh=ingestion_full_refresh,
    )

    dlt_source = slack.slack_source(
        selected_channels=selected_channels,
        replies=True,
    )

    load_info = slack_pipeline.run(dlt_source)
    print(load_info)

    if os.environ.get("OPENAI_API_KEY") is None:
        raise KeyError("OPENAI_API_KEY wasn't set.")

    # hamilton
    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_modules(transform)
        .build()
    )
    dr.display_all_functions("dag_transform.png", orient="TB")

    inputs = dict(
        selected_channels=selected_channels,
        pipeline=slack_pipeline,
    )
    dr.execute(["insert_threads"], inputs=inputs)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("channels", nargs="+", type=str, help="Slack channels to load.")
    parser.add_argument("--full-refresh", action="store_true", help="Reload all Slack data.")

    args = parser.parse_args()

    main(selected_channels=args.channels, ingestion_full_refresh=args.full_refresh)
