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
