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

from typing import Any

from hamilton.htypes import Collect, Parallelizable


def mapper(
    drivers: list,
    inputs: list,
    final_vars: list = None,
) -> Parallelizable[dict]:
    if final_vars is None:
        final_vars = []
    for dr, input_ in zip(drivers, inputs):
        yield {
            "dr": dr,
            "final_vars": final_vars or dr.list_available_variables(),
            "input": input_,
        }


def inside(mapper: dict) -> dict:
    _dr = mapper["dr"]
    _inputs = mapper["input"]
    _final_var = mapper["final_vars"]
    return _dr.execute(final_vars=_final_var, inputs=_inputs)


def passthrough(inside: dict) -> dict:
    return inside


def reducer(passthrough: Collect[dict]) -> Any:
    return passthrough
