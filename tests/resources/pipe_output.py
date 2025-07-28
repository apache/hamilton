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

from hamilton.function_modifiers import pipe_output, source, step, value


def _pipe_output0(x: str) -> str:
    return x + "-post pipe 0-"


def _pipe_output1(x: str, upstream: str) -> str:
    return x + f"-post pipe 1 with {upstream}-"


def _pipe_output2(x: str, some_val: int) -> str:
    return x + f"-post pipe 2 with value {some_val}-"


def upstream() -> str:
    return "-upstream-"


def user_input() -> str:
    return "-user input-"


@pipe_output(
    step(_pipe_output0),
    step(_pipe_output1, upstream=source("upstream")).named("random"),
    step(_pipe_output2, some_val=value(1000)),
)
def f_of_interest(user_input: str) -> str:
    return user_input + "-raw function-"


def downstream_f(f_of_interest: str) -> str:
    return f_of_interest + "-downstream."


def chain_not_using_pipe_output() -> str:
    t = downstream_f(
        _pipe_output2(_pipe_output1(_pipe_output0(f_of_interest(user_input())), upstream()), 1000)
    )
    return t


def _add_one(v: int) -> int:
    return v + 1


def _add_two(v: int) -> int:
    return v + 2


def _add_n(v: int, n: int) -> int:
    return v + n


def _multiply_n(v: int, *, n: int) -> int:
    return v * n


def _square(v: int) -> int:
    return v * v


def v() -> int:
    return 10


@pipe_output(
    step(_add_one).named("a"),
    step(_add_two).named("b"),
    step(_add_n, n=3).named("c").when(calc_c=True),
    step(_add_n, n=source("input_1")).named("d"),
    step(_multiply_n, n=source("input_2")).named("e"),
)
def chain_1_using_pipe_output(v: int) -> int:
    return v * 10


def chain_1_not_using_pipe_output(v: int, input_1: int, input_2: int, calc_c: bool = False) -> int:
    start = v * 10
    a = _add_one(start)
    b = _add_two(a)
    c = _add_n(b, n=3) if calc_c else b
    d = _add_n(c, n=input_1)
    e = _multiply_n(d, n=input_2)
    return e


@pipe_output(
    step(_square).named("a"),
    step(_multiply_n, n=value(2)).named("b"),
    step(_add_n, n=10).named("c").when(calc_c=True),
    step(_add_n, n=source("input_3")).named("d"),
    step(_add_two).named("e"),
)
def chain_2_using_pipe_output(v: int) -> int:
    return v + 10


def chain_2_not_using_pipe_output(v: int, input_3: int, calc_c: bool = False) -> int:
    start = v + 10
    a = _square(start)
    b = _multiply_n(a, n=2)
    c = _add_n(b, n=10) if calc_c else b
    d = _add_n(c, n=input_3)  # Assuming "upstream" refers to the same value as "v" here
    e = _add_two(d)
    return e


@pipe_output(
    step(_square).named("a").when(key="Yes"),
    step(_multiply_n, n=value(2)).named("b").when(key="No"),
    step(_add_n, n=10).named("c").when(key="Yes"),
    step(_add_n, n=source("input_3")).named("d").when(key="No"),
    step(_add_two).named("e").when(key="Yes"),
)
def chain_3_using_pipe_output(v: int) -> int:
    return v + 10


def chain_3_not_using_pipe_output_config_true(v: int, input_3: int) -> int:
    start = v + 10
    a = _square(start)
    c = _add_n(a, n=10)
    e = _add_two(c)
    return e


def chain_3_not_using_pipe_output_config_false(v: int, input_3: int) -> int:
    start = v + 10
    b = _multiply_n(start, n=2)
    d = _add_n(b, n=input_3)
    return d


def chain_3_not_using_pipe_output_config_no_conditions_met(v: int, input_3: int) -> int:
    start = v + 10
    return start
