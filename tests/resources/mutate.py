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

from hamilton.function_modifiers import apply_to, mutate, source, value


def upstream() -> str:
    return "-upstream-"


def user_input() -> str:
    return "-user input-"


def f_of_interest(user_input: str) -> str:
    return user_input + "-raw function-"


def downstream_f(f_of_interest: str) -> str:
    return f_of_interest + "-downstream."


@mutate(f_of_interest)
def _mutate0(x: str) -> str:
    return x + "-post pipe 0-"


@mutate(apply_to(f_of_interest, upstream=source("upstream")).named("random"))
def _mutate1(x: str, upstream: str) -> str:
    return x + f"-post pipe 1 with {upstream}-"


@mutate(apply_to(f_of_interest, some_val=value(1000)))
def _mutate2(x: str, some_val: int) -> str:
    return x + f"-post pipe 2 with value {some_val}-"


def chain_not_using_mutate() -> str:
    t = downstream_f(_mutate2(_mutate1(_mutate0(f_of_interest(user_input())), upstream()), 1000))
    return t


def v() -> int:
    return 10


def chain_1_using_mutate(v: int) -> int:
    return v * 10


def chain_1_not_using_mutate(v: int, input_1: int, input_2: int, calc_c: bool = False) -> int:
    start = v * 10
    a = _add_one(start)
    b = _add_two(a)
    c = _add_n(b, n=3) if calc_c else b
    d = _add_n(c, n=input_1)
    e = _multiply_n(d, n=input_2)
    return e


def chain_2_using_mutate(v: int) -> int:
    return v + 10


def chain_2_not_using_mutate(v: int, input_3: int, calc_c: bool = False) -> int:
    start = v + 10
    a = _square(start)
    b = _multiply_n(a, n=2)
    return b


@mutate(
    apply_to(chain_2_using_mutate).named("a"),
)
def _square(v: int) -> int:
    return v * v


@mutate(
    apply_to(chain_1_using_mutate).named("a"),
)
def _add_one(v: int) -> int:
    return v + 1


@mutate(
    apply_to(chain_1_using_mutate).named("b"),
)
def _add_two(v: int) -> int:
    return v + 2


@mutate(
    apply_to(chain_1_using_mutate, n=3).named("c").when(calc_c=True),
    apply_to(chain_1_using_mutate, n=source("input_1")).named("d"),
)
def _add_n(v: int, n: int) -> int:
    return v + n


@mutate(
    apply_to(chain_1_using_mutate).named("e"),
    apply_to(chain_2_using_mutate, n=value(2)).named("b"),
    n=source("input_2"),
)
def _multiply_n(v: int, *, n: int) -> int:
    return v * n
