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


async def a() -> str:
    print("a")
    await asyncio.sleep(3)
    return "a"


async def b() -> str:
    print("b")
    await asyncio.sleep(3)
    return "b"


async def c(a: str, b: str) -> str:
    print("c")
    await asyncio.sleep(3)
    return a + " " + b


async def d() -> str:
    print("d")
    await asyncio.sleep(3)
    return "d"


async def e(c: str, d: str) -> str:
    print("e")
    await asyncio.sleep(3)
    return c + " " + d


async def z() -> str:
    print("z")
    await asyncio.sleep(3)
    return "z"


async def y() -> str:
    print("y")
    await asyncio.sleep(3)
    return "y"


async def x(z: str, y: str) -> str:
    print("x")
    await asyncio.sleep(3)
    return z + " " + y


async def s(x: str, e: str) -> str:
    print("s")
    await asyncio.sleep(3)
    return x + " " + e
