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

# input
def number_of_steps() -> int:
    return 5


# process
def steps(number_of_steps: int) -> int:
    return number_of_steps


# process
def step_squared(steps: int) -> int:
    print("squaring step {}".format(steps))
    return steps**2


# process
def step_cubed(steps: int) -> int:
    print("cubing step {}".format(steps))
    return steps**3


def step_squared_plus_step_cubed(step_squared: int, step_cubed: int) -> int:
    print("adding step squared and step cubed")
    return step_squared + step_cubed


def sum_step_squared_plus_step_cubed(step_squared_plus_step_cubed: int) -> int:
    print("summing step squared")
    return step_squared_plus_step_cubed


# final
def final(sum_step_squared_plus_step_cubed: int) -> int:
    print("finalizing")
    return sum_step_squared_plus_step_cubed


def _calc():
    number_of_steps_ = number_of_steps()
    steps_ = steps(number_of_steps_)
    step_squared_ = step_squared(steps_)
    step_cubed_ = step_cubed(steps_)
    step_squared_plus_step_cubed_ = step_squared_plus_step_cubed(step_squared_, step_cubed_)
    sum_step_squared_plus_step_cubed_ = sum_step_squared_plus_step_cubed(
        step_squared_plus_step_cubed_
    )
    final_ = final(sum_step_squared_plus_step_cubed_)
    return final_
