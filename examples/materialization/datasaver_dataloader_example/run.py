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

import simple_etl

from hamilton import driver
from hamilton_sdk import adapters

tracker = adapters.HamiltonTracker(
    project_id=7,  # modify this as needed
    username="elijah@dagworks.io",  # modify this as needed
    dag_name="my_example_dag",
    tags={"environment": "DEV", "team": "MY_TEAM", "version": "X"},
)

dr = driver.Builder().with_config({}).with_modules(simple_etl).with_adapters(tracker).build()
dr.display_all_functions("simple_etl.png")

import time

start = time.time()
print(start)
dr.execute(["saved_data"], inputs={"filepath": "data.csv"})
print(time.time() - start)
