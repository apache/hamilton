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

import asyncio
import json
import logging

import aiohttp
import fastapi

logger = logging.getLogger(__name__)


async def request_raw(request: fastapi.Request) -> dict:
    try:
        return await request.json()
    except json.JSONDecodeError as e:
        logger.warning(f"Unable to get JSON from request. Error is:\n{e}")
        return {}


def foo(request_raw: dict) -> str:
    return request_raw.get("foo", "far")


def bar(request_raw: dict) -> str:
    return request_raw.get("bar", "baz")


async def some_data() -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get("http://httpbin.org/get") as resp:
            return await resp.json()


async def computation1(foo: str, some_data: dict) -> bool:
    await asyncio.sleep(1)
    return False


async def computation2(bar: str) -> bool:
    await asyncio.sleep(1)
    return True


async def pipeline(computation1: bool, computation2: bool) -> dict:
    await asyncio.sleep(1)
    return {"computation1": computation1, "computation2": computation2}
