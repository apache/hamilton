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

"""
Shows how to run document chunking using ray.
"""

import logging

import doc_pipeline
import ray

from hamilton import driver, log_setup
from hamilton.plugins import h_ray

if __name__ == "__main__":
    log_setup.setup_logging(logging.INFO)
    ray.init()

    dr = (
        driver.Builder()
        .with_modules(doc_pipeline)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_config({})
        # Choose a backend to process the parallel parts of the pipeline
        # .with_remote_executor(executors.MultiThreadingExecutor(max_tasks=5))
        # .with_remote_executor(executors.MultiProcessingExecutor(max_tasks=5))
        .with_remote_executor(
            h_ray.RayTaskExecutor()
        )  # be sure to run ray.init() or pass in config.
        .build()
    )
    dr.display_all_functions("pipeline.png")
    result = dr.execute(
        ["collect_chunked_url_text"],
        inputs={"chunk_size": 256, "chunk_overlap": 32},
    )
    # do something with the result...
    import pprint

    for chunk in result["collect_chunked_url_text"]:
        pprint.pprint(chunk)

    ray.shutdown()
