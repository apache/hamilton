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

from hamilton.function_modifiers import parameterize_sources, parametrized_input


def input_1() -> int:
    return 1


def input_2() -> int:
    return 2


def input_3() -> int:
    return 3


@parametrized_input(
    parameter="input_value_tbd",
    variable_inputs={
        "input_1": ("output_1", "function_with_multiple_inputs called using input_1"),
        "input_2": ("output_2", "function_with_multiple_inputs called using input_2"),
    },
)
def function_with_multiple_inputs(input_value_tbd: int, static_value: int) -> int:
    return input_value_tbd + static_value


# We don't prefer this style of specifying the values. i.e. kwarg with {}.
@parameterize_sources(output_12={"input_value_tbd1": "input_1", "input_value_tbd2": "input_2"})
def function_with_two_parameters(
    input_value_tbd1: int, input_value_tbd2: int, static_value: int
) -> int:
    """function_with_multiple_inputs called using {input_value_tbd1} and {input_value_tbd2}

    :return: creates {output_name}
    """
    return input_value_tbd1 + input_value_tbd2 + static_value


# We prefer this style of specifying the values. i.e. kwarg with dict().
@parameterize_sources(
    output_123=dict(
        input_value_tbd1="input_1", input_value_tbd2="input_2", input_value_tbd3="input_3"
    )
)
def function_with_three_parameters(
    input_value_tbd1: int, input_value_tbd2: int, input_value_tbd3: int, static_value: int
) -> int:
    """function_with_multiple_inputs called using {input_value_tbd1} and {input_value_tbd2} and {input_value_tbd3}

    :param {input_value_tbd1}:
    :param {input_value_tbd2}:
    :param {input_value_tbd3}:
    :param static_value:
    :return: {output_name}
    """
    return input_value_tbd1 + input_value_tbd2 + input_value_tbd3 + static_value
