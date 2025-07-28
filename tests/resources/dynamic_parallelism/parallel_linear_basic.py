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


# input
def number_of_steps() -> int:
    return 6


# expand
def steps(number_of_steps: int) -> Parallelizable[int]:
    yield from range(number_of_steps)


# process
def step_squared(steps: int) -> int:
    return steps**2


# process
def step_cubed(steps: int) -> int:
    return steps**3


def step_squared_plus_step_cubed(step_squared: int, step_cubed: int) -> int:
    return step_squared + step_cubed


# join
def sum_step_squared_plus_step_cubed(step_squared_plus_step_cubed: Collect[int]) -> int:
    out = 0
    for step in step_squared_plus_step_cubed:
        out += step
    return out


# final
def final(sum_step_squared_plus_step_cubed: int) -> int:
    return sum_step_squared_plus_step_cubed


def _calc(number_of_steps: int = number_of_steps()) -> int:
    steps_ = steps(number_of_steps)
    to_sum = []
    for step_ in steps_:
        step_squared_ = step_squared(step_)
        step_cubed_ = step_cubed(step_)
        step_squared_plus_step_cubed_ = step_squared_plus_step_cubed(step_squared_, step_cubed_)
        to_sum.append(step_squared_plus_step_cubed_)
    sum_step_squared_plus_step_cubed_ = sum_step_squared_plus_step_cubed(to_sum)
    final_ = final(sum_step_squared_plus_step_cubed_)
    return final_
