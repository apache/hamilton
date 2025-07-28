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

from hamilton import common, driver

import tests.resources.cyclic_functions
import tests.resources.test_default_args


class Object:
    """Dummy class to test with."""

    def __repr__(self):
        return "'object'"


@pytest.mark.parametrize(
    "value_to_convert, module_set, expected_value, expected_error",
    [
        ("a", {"amodule"}, "a", None),
        (
            tests.resources.test_default_args.A,
            {tests.resources.test_default_args.__name__},
            "A",
            None,
        ),
        (
            driver.Variable("A", int, {}, False, (), None, set(), set(), {}),
            {"amodule"},
            "A",
            None,
        ),
        (
            Object(),
            {"amodule"},
            None,
            "Materializer dependency 'object' is not a string, a function, or a driver.Variable.",
        ),
        (
            tests.resources.cyclic_functions.A,
            {tests.resources.test_default_args.__name__},
            None,
            "Function tests.resources.cyclic_functions.A is a function not in a module given to the materializer. Valid choices are {'tests.resources.test_default_args'}.",
        ),
    ],
)
def test_convert_output_value(value_to_convert, module_set, expected_value, expected_error):
    actual_value, actual_error = common.convert_output_value(value_to_convert, module_set)
    assert actual_value == expected_value
    assert actual_error == expected_error


def test_convert_output_values_happy():
    """Tests that we loop as expected without issue"""
    actual = common.convert_output_values(
        [tests.resources.test_default_args.A, "B"], {tests.resources.test_default_args.__name__}
    )
    assert actual == ["A", "B"]


def test_convert_output_values_error():
    """Tests that we error when bad cases are encountered."""
    with pytest.raises(ValueError):
        common.convert_output_values(
            [tests.resources.test_default_args.A, tests.resources.cyclic_functions.A],
            {tests.resources.test_default_args.__name__},
        )
