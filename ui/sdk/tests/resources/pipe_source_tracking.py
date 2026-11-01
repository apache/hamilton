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

from hamilton.function_modifiers import mutate, pipe_input, pipe_output, step


def _increment(value: int) -> int:
    return value + 1


@pipe_input(step(_increment).named("increment"))
def input_pipe(value: int) -> int:
    return value * 2


@pipe_output(step(_increment).named("increment"))
def output_pipe(value: int) -> int:
    return value * 2


def mutated(value: int) -> int:
    return value * 2


@mutate(mutated)
def _mutator(value: int) -> int:
    return value + 1
