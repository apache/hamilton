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

import pandas as pd

from hamilton.function_modifiers import pipe_input, pipe_output, step

# async def data_input() -> pd.DataFrame:
#     await asyncio.sleep(0.0001)
#     return


async def _groupby_a(d: pd.DataFrame) -> pd.DataFrame:
    await asyncio.sleep(0.0001)
    return d.groupby("a").sum().reset_index()


async def _groupby_b(d: pd.DataFrame) -> pd.DataFrame:
    await asyncio.sleep(0.0001)
    return d.groupby("b").sum().reset_index()


@pipe_input(
    step(_groupby_a).when(groupby="a"),
    step(_groupby_b).when_not(groupby="a"),
)
def data_pipe_input(data_input: pd.DataFrame) -> pd.DataFrame:
    return data_input


@pipe_output(
    step(_groupby_a).when(groupby="a"),
    step(_groupby_b).when_not(groupby="a"),
)
def data_pipe_output(data_input: pd.DataFrame) -> pd.DataFrame:
    return data_input
