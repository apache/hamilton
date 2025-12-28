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

import dataflow
from mock_api import DataGeneratorResource

from hamilton import driver
from hamilton.io.materialization import to
from hamilton.plugins import matplotlib_extensions  # noqa: F401


def main():
    dr = driver.Builder().with_modules(dataflow).build()
    dr.display_all_functions("all_functions.png")

    inputs = dict(
        hackernews_api=DataGeneratorResource(num_days=30),
    )

    materializers = [
        to.json(
            id="topstory_ids.json",
            dependencies=["topstory_ids"],
            path="./topstory_ids.json",
        ),
        to.json(
            id="most_frequent_words.json",
            dependencies=["most_frequent_words"],
            path="./most_frequent_words.json",
        ),
        to.csv(
            id="topstories.csv",
            dependencies=["topstories"],
            path="./topstories.csv",
        ),
        to.csv(
            id="signups.csv",
            dependencies=["signups"],
            path="./signups.csv",
        ),
        to.plt(
            id="top_25_words_plot.plt",
            dependencies=["top_25_words_plot"],
            path="./top_25_words_plot.png",
        ),
    ]

    dr.visualize_materialization(*materializers, inputs=inputs, output_file_path="dataflow.png")
    dr.materialize(*materializers, inputs=inputs)


if __name__ == "__main__":
    main()
