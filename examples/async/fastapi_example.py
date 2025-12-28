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

import logging
from contextlib import asynccontextmanager

import aiohttp
import async_module
import fastapi
from aiohttp import client_exceptions

from hamilton import async_driver
from hamilton_sdk import adapters

logger = logging.getLogger(__name__)

# can instantiate a driver once for the life of the app:
dr_with_tracking: async_driver.AsyncDriver = None
dr_without_tracking: async_driver.AsyncDriver = None


async def _tracking_server_running():
    """Quickly tells if the tracking server is up and running"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8241/api/v1/ping") as response:
                if response.status == 200:
                    return True
                else:
                    return False
        except client_exceptions.ClientConnectionError:
            return False


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    """Fast API lifespan context manager for setting up the driver and tracking adapters
    This has to be done async as there are initializers
    """
    global dr_with_tracking
    global dr_without_tracking
    builder = async_driver.Builder().with_modules(async_module)
    is_server_running = await _tracking_server_running()
    dr_without_tracking = await builder.build()
    dr_with_tracking = (
        await builder.with_adapters(
            adapters.AsyncHamiltonTracker(
                project_id=1,
                username="elijah",
                dag_name="async_tracker",
            )
        ).build()
        if is_server_running
        else None
    )
    if not is_server_running:
        logger.warning(
            "Tracking server is not running, skipping telemetry. To run the telemetry server, run hamilton ui. "
            "Note you must have a project with ID 1 if it is running -- if not, you can change the project "
            "ID in this file or create a new one from the UI. Then make sure to restart this server."
        )
    yield


app = fastapi.FastAPI(lifespan=lifespan)


@app.post("/execute")
async def call_without_tracker(request: fastapi.Request) -> dict:
    """Handler for pipeline call -- this does not track in the Hamilton UI"""
    input_data = {"request": request}
    result = await dr_without_tracking.execute(["pipeline"], inputs=input_data)
    # dr.visualize_execution(["pipeline"], "./pipeline.dot", {"format": "png"}, inputs=input_data)
    return result


@app.post("/execute_tracker")
async def call_with_tracker(request: fastapi.Request) -> dict:
    """Handler for pipeline call -- this does track in the Hamilton UI."""
    input_data = {"request": request}
    if dr_with_tracking is None:
        raise ValueError(
            "Tracking driver not initialized -- you must have the tracking server running at app startup to use this endpoint."
        )
    result = await dr_with_tracking.execute(["pipeline"], inputs=input_data)
    # dr.visualize_execution(["pipeline"], "./pipeline.dot", {"format": "png"}, inputs=input_data)
    return result


if __name__ == "__main__":
    # If you run this as a script, then the app will be started on localhost:8000
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
