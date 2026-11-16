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

import pytest

from hamilton import ad_hoc_utils, driver
from hamilton.lifecycle import default

from tests.resources import mismatched_types


def test_noedge_input_type_checking_without_adapter():
    with pytest.raises(ValueError):
        driver.Builder().with_modules(mismatched_types).build()


def test_noedge_input_type_checking_with_adapter():
    dr = (
        driver.Builder()
        .with_modules(mismatched_types)
        .with_adapters(default.NoEdgeAndInputTypeChecking())
        .build()
    )
    actual = dr.execute(["baz"], inputs={"a": 1.02, "number": "aaasdfdsf"})
    assert actual == {"baz": "1.02 2 aaasdfdsf"}


def test_function_input_output_type_checker_handles_pep604_union_of_generics():
    def evens(n: int) -> list[int] | None:
        return [i * 2 for i in range(n)] if n else None

    def total(evens: list[int] | None) -> int:
        return sum(evens or [])

    dr = (
        driver.Builder()
        .with_modules(ad_hoc_utils.create_temporary_module(evens, total))
        .with_adapters(default.FunctionInputOutputTypeChecker())
        .build()
    )
    assert dr.execute(["total"], inputs={"n": 3}) == {"total": 6}
    assert dr.execute(["total"], inputs={"n": 0}) == {"total": 0}


def test_function_input_output_type_checker_rejects_wrong_pep604_union_result():
    def evens(n: int) -> list[int] | None:
        return ["not", "ints"]

    dr = (
        driver.Builder()
        .with_modules(ad_hoc_utils.create_temporary_module(evens))
        .with_adapters(default.FunctionInputOutputTypeChecker())
        .build()
    )
    with pytest.raises(TypeError, match="Node evens returned a result"):
        dr.execute(["evens"], inputs={"n": 3})


def test_function_input_output_type_checker_handles_fixed_length_tuple():
    def get_pair() -> tuple[int, str]:
        return (42, "hello")

    def format_pair(get_pair: tuple[int, str]) -> str:
        num, text = get_pair
        return f"{text}:{num}"

    dr = (
        driver.Builder()
        .with_modules(ad_hoc_utils.create_temporary_module(get_pair, format_pair))
        .with_adapters(default.FunctionInputOutputTypeChecker())
        .build()
    )
    res = dr.execute(["format_pair"])
    assert res == {"format_pair": "hello:42"}


def test_function_input_output_type_checker_rejects_wrong_length_tuple_result():
    def get_pair() -> tuple[int, str]:
        return (42,)

    dr = (
        driver.Builder()
        .with_modules(ad_hoc_utils.create_temporary_module(get_pair))
        .with_adapters(default.FunctionInputOutputTypeChecker())
        .build()
    )
    with pytest.raises(TypeError, match="Node get_pair returned a result"):
        dr.execute(["get_pair"])


def test_function_input_output_type_checker_rejects_wrong_type_tuple_result():
    def get_pair() -> tuple[int, str]:
        return ("hello", 42)

    dr = (
        driver.Builder()
        .with_modules(ad_hoc_utils.create_temporary_module(get_pair))
        .with_adapters(default.FunctionInputOutputTypeChecker())
        .build()
    )
    with pytest.raises(TypeError, match="Node get_pair returned a result"):
        dr.execute(["get_pair"])


def test_function_input_output_type_checker_rejects_wrong_tuple_node_input():
    def produce_pair() -> Any:
        return (42,)

    def consume_pair(produce_pair: tuple[int, str]) -> str:
        return f"{produce_pair[0]}"

    dr = (
        driver.Builder()
        .with_modules(ad_hoc_utils.create_temporary_module(produce_pair, consume_pair))
        .with_adapters(default.FunctionInputOutputTypeChecker(check_output=False, check_input=True))
        .build()
    )
    with pytest.raises(TypeError, match="Node consume_pair received an input"):
        dr.execute(["consume_pair"])


def test_function_input_output_type_checker_handles_empty_tuple():
    def empty_node() -> tuple[()]:
        return ()

    dr = (
        driver.Builder()
        .with_modules(ad_hoc_utils.create_temporary_module(empty_node))
        .with_adapters(default.FunctionInputOutputTypeChecker())
        .build()
    )
    res = dr.execute(["empty_node"])
    assert res == {"empty_node": ()}


def test_function_input_output_type_checker_rejects_non_empty_tuple_for_empty_tuple_type():
    def empty_node() -> tuple[()]:
        return (1,)

    dr = (
        driver.Builder()
        .with_modules(ad_hoc_utils.create_temporary_module(empty_node))
        .with_adapters(default.FunctionInputOutputTypeChecker())
        .build()
    )
    with pytest.raises(TypeError, match="Node empty_node returned a result"):
        dr.execute(["empty_node"])
