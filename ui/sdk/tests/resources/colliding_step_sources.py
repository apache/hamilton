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

from hamilton.function_modifiers import pipe_input, pipe_output, step


def _make_step(add):
    if add:

        def transform(value: int) -> int:
            return value + 1

    else:

        def transform(value: int) -> int:
            return value * 3

    return transform


def _make_lambdas():
    functions = (
        lambda value: value + 2,
        lambda value: value * 5,
    )
    for function in functions:
        function.__annotations__ = {"value": int, "return": int}
    return functions


_steps = (_make_step(True), _make_step(False), *_make_lambdas())


@pipe_input(
    step(_steps[0]).named("first"),
    step(_steps[1]).named("second"),
    step(_steps[2]).named("lambda_add"),
    step(_steps[3]).named("lambda_multiply"),
)
def input_chain(value: int) -> int:
    return value


@pipe_output(
    step(_steps[0]).named("first"),
    step(_steps[1]).named("second"),
    step(_steps[2]).named("lambda_add"),
    step(_steps[3]).named("lambda_multiply"),
)
def output_chain(value: int) -> int:
    return value
