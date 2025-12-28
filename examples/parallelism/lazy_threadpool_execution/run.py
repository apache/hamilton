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

import time

import my_functions

from hamilton import async_driver, driver
from hamilton.plugins import h_threadpool

start = time.time()
adapter = h_threadpool.FutureAdapter()
dr = driver.Builder().with_modules(my_functions).with_adapters(adapter).build()
dr.display_all_functions("my_functions.png")
r = dr.execute(["s", "x", "a"])
print("got return from dr")
print(r)
print("Time taken with", time.time() - start)

from hamilton_sdk import adapters

tracker = adapters.HamiltonTracker(
    project_id=21,  # modify this as needed
    username="elijah@dagworks.io",
    dag_name="with_caching",
    tags={"environment": "DEV", "cached": "False", "team": "MY_TEAM", "version": "1"},
)

start = time.time()
dr = (
    driver.Builder().with_modules(my_functions).with_adapters(tracker, adapter).with_cache().build()
)
r = dr.execute(["s", "x", "a"])
print("got return from dr")
print(r)
print("Time taken with cold cache", time.time() - start)

tracker = adapters.HamiltonTracker(
    project_id=21,  # modify this as needed
    username="elijah@dagworks.io",
    dag_name="with_caching",
    tags={"environment": "DEV", "cached": "True", "team": "MY_TEAM", "version": "1"},
)

start = time.time()
dr = (
    driver.Builder().with_modules(my_functions).with_adapters(tracker, adapter).with_cache().build()
)
r = dr.execute(["s", "x", "a"])
print("got return from dr")
print(r)
print("Time taken with warm cache", time.time() - start)

start = time.time()
dr = driver.Builder().with_modules(my_functions).build()
r = dr.execute(["s", "x", "a"])
print("got return from dr")
print(r)
print("Time taken without", time.time() - start)


async def run_async():
    import my_functions_async

    start = time.time()
    dr = await async_driver.Builder().with_modules(my_functions_async).build()
    dr.display_all_functions("my_functions_async.png")
    r = await dr.execute(["s", "x", "a"])
    print("got return from dr")
    print(r)
    print("Async Time taken without", time.time() - start)


import asyncio

asyncio.run(run_async())
