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

from hamilton import function_modifiers
from hamilton.function_modifiers import expanders
from hamilton.function_modifiers.configuration import config
from hamilton.function_modifiers.recursive import subdag


def a() -> int:
    return 1


def b() -> int:
    return 2


def _get_submodules():
    """Utility function to gather fns for reuse so they don't get included in the general function graph"""

    @config.when(op="add")
    def d__add(a: int, c: int) -> int:
        return a + c

    @config.when(op="subtract")
    def d__subtract(a: int, c: int) -> int:
        return a - c

    def e(c: int) -> int:
        return c * 2

    def f(c: int, b: int, e: int) -> int:
        return c + b + e

    submodules = [d__add, d__subtract, e, f]
    return submodules


submodules = _get_submodules()


@subdag(
    *_get_submodules(),
    inputs={"c": function_modifiers.value(10)},
    config={"op": "subtract"},
)
def v1(e: int, f: int) -> dict:
    return {"e_1": e, "f_1": f}


@subdag(
    *_get_submodules(),
    inputs={"c": function_modifiers.value(20)},
    config={"op": "subtract"},
)
def v2(e: int, f: int) -> dict:
    return {"e_2": e, "f_2": f}


@subdag(
    *_get_submodules(),
    inputs={"c": function_modifiers.value(30)},
    config={"op": "add"},
)
def v3(e: int, f: int) -> dict:
    return {"e_3": e, "f_3": f}


@subdag(
    *_get_submodules(),
    inputs={"c": function_modifiers.source("b")},
    config={"op": "add"},
)
def v4(e: int, f: int) -> dict:
    return {"e_4": e, "f_4": f}


# This is a little messy because we can't currently use @extract_fields
# in conjunction with @subdag. So we just extract afterwards..
@expanders.parameterize(
    e_1={"output": function_modifiers.source("v1"), "field": function_modifiers.value("e_1")},
    f_1={"output": function_modifiers.source("v1"), "field": function_modifiers.value("f_1")},
    e_2={"output": function_modifiers.source("v2"), "field": function_modifiers.value("e_2")},
    f_2={"output": function_modifiers.source("v2"), "field": function_modifiers.value("f_2")},
    e_3={"output": function_modifiers.source("v3"), "field": function_modifiers.value("e_3")},
    f_3={"output": function_modifiers.source("v3"), "field": function_modifiers.value("f_3")},
    e_4={"output": function_modifiers.source("v4"), "field": function_modifiers.value("e_4")},
    f_4={"output": function_modifiers.source("v4"), "field": function_modifiers.value("f_4")},
)
def extract_all(output: dict, field: str) -> int:
    return output[field]


def _sum(**kwargs: int) -> int:
    return sum(kwargs.values())


@function_modifiers.does(_sum)
def sum_everything(
    e_1: int, e_2: int, e_3: int, e_4: int, f_1: int, f_2: int, f_3: int, f_4: int
) -> int:
    pass
