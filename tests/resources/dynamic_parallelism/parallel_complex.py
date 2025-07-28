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

from hamilton.htypes import Collect, Parallelizable


def number_of_steps() -> int:
    return 5


def param_external_to_block() -> int:
    return 3


def second_param_external_to_block() -> int:
    return 4


def steps(number_of_steps: int) -> Parallelizable[int]:
    yield from range(number_of_steps)


# Parallelizable block Start


def step_modified(steps: int, second_param_external_to_block: int) -> int:
    return steps + second_param_external_to_block


def double_step(step_modified: int) -> int:
    return step_modified * 2


def triple_step(step_modified: int) -> int:
    return step_modified * 3


def double_plus_triple_step(double_step: int, triple_step: int) -> int:
    return double_step + triple_step


def double_plus_triple_plus_param_external_to_block(
    double_plus_triple_step: int, param_external_to_block: int
) -> int:
    return double_plus_triple_step + param_external_to_block


# Parallelizable block ends here


def sum_of_some_things(double_plus_triple_plus_param_external_to_block: Collect[int]) -> int:
    return sum(double_plus_triple_plus_param_external_to_block)


def final(sum_of_some_things: int) -> int:
    return sum_of_some_things
