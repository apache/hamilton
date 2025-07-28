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

from hamilton.function_modifiers import apply_to, mutate


def data_mutate(data_input: pd.DataFrame) -> pd.DataFrame:
    return data_input


@mutate(apply_to(data_mutate).when(groupby="a"))
async def _groupby_a_mutate(d: pd.DataFrame) -> pd.DataFrame:
    await asyncio.sleep(0.0001)
    return d.groupby("a").sum().reset_index()


@mutate(apply_to(data_mutate).when_not(groupby="a"))
async def _groupby_b_mutate(d: pd.DataFrame) -> pd.DataFrame:
    await asyncio.sleep(0.0001)
    return d.groupby("b").sum().reset_index()
