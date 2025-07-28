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

from hamilton.function_modifiers import pipe_input, source, step, value


def _add_one(v: int) -> int:
    return v + 1


def _add_n(v: int, n: int) -> int:
    return v + n


def _multiply_n(v: int, *, n: int) -> int:
    return v * n


def _add_two(v: int) -> int:
    return v + 2


def _square(v: int) -> int:
    return v * v


def v() -> int:
    return 10


def w() -> int:
    return 100


@pipe_input(
    step(_add_one).named("a"),
    step(_add_two).named("b"),
    step(_add_n, n=3).named("c").when(calc_c=True),
    step(_add_n, n=source("input_1")).named("d"),
    step(_multiply_n, n=source("input_2")).named("e"),
)
def chain_1_using_pipe(v: int) -> int:
    return v * 10


def chain_1_not_using_pipe(v: int, input_1: int, input_2: int, calc_c: bool = False) -> int:
    a = _add_one(v)
    b = _add_two(a)
    c = _add_n(b, n=3) if calc_c else b
    d = _add_n(c, n=input_1)
    e = _multiply_n(d, n=input_2)
    return e * 10


@pipe_input(
    step(_square).named("a"),
    step(_multiply_n, n=value(2)).named("b"),
    step(_add_n, n=10).named("c").when(calc_c=True),
    step(_add_n, n=source("input_3")).named("d"),
    step(_add_two).named("e"),
)
def chain_2_using_pipe(v: int) -> int:
    return v + 10


def chain_2_not_using_pipe(v: int, input_3: int, calc_c: bool = False) -> int:
    a = _square(v)
    b = _multiply_n(a, n=2)
    c = _add_n(b, n=10) if calc_c else b
    d = _add_n(c, n=input_3)  # Assuming "upstream" refers to the same value as "v" here
    e = _add_two(d)
    return e + 10


@pipe_input(
    step(_add_one).named("a"),
    step(_add_two).named("b"),
    step(_add_n, n=3).named("c").when(calc_c=True),
    step(_add_n, n=source("input_1")).named("d"),
    step(_multiply_n, n=source("input_2")).named("e"),
    on_input="w",
    namespace="global",
)
def chain_1_using_pipe_input_target_global(v: int, w: int) -> int:
    return v + w * 10


def chain_1_not_using_pipe_input_target_global(
    v: int, w: int, input_1: int, input_2: int, calc_c: bool = False
) -> int:
    a = _add_one(w)
    b = _add_two(a)
    c = _add_n(b, n=3) if calc_c else b
    d = _add_n(c, n=input_1)
    e = _multiply_n(d, n=input_2)
    return v + e * 10


# TODO: for tests in case of multiple target parameters
# @pipe_input(
#     step(_add_one).on_input(["v", "w"]).named("a"),
#     step(_add_two).on_input("v").named("b"),
#     step(_add_n, n=3).on_input("w").named("c").when(calc_c=True),
#     step(_add_n, n=source("input_1")).on_input("v").named("d"),
#     step(_multiply_n, n=source("input_2")).on_input("w").named("e"),
#     namespace="local",
# )
# def chain_1_using_pipe_input_target_local(v: int, w: int) -> int:
#     return v + w * 10


# def chain_1_not_using_pipe_input_target_local(
#     v: int, w: int, input_1: int, input_2: int, calc_c: bool = False
# ) -> int:
#     av = _add_one(v)
#     aw = _add_one(w)
#     bv = _add_two(av)
#     cw = _add_n(aw, n=3) if calc_c else aw
#     dv = _add_n(bv, n=input_1)
#     ew = _multiply_n(cw, n=input_2)
#     return dv + ew * 10


# @pipe_input(
#     step(_add_one).on_input("w").named("a"),
#     step(_add_two).named("b"),
#     step(_add_n, n=3).on_input("w").named("c").when(calc_c=True),
#     step(_add_n, n=source("input_1")).named("d"),
#     step(_multiply_n, n=source("input_2")).on_input("w").named("e"),
#     namespace="mixed",
#     on_input="v",
# )
# def chain_1_using_pipe_input_target_mixed(v: int, w: int) -> int:
#     return v + w * 10


# def chain_1_not_using_pipe_input_target_mixed(
#     v: int, w: int, input_1: int, input_2: int, calc_c: bool = False
# ) -> int:
#     av = _add_one(v)
#     aw = _add_one(w)
#     bv = _add_two(av)
#     cv = _add_n(bv, n=3) if calc_c else bv
#     cw = _add_n(aw, n=3) if calc_c else aw
#     dv = _add_n(cv, n=input_1)
#     ev = _multiply_n(dv, n=input_2)
#     ew = _multiply_n(cw, n=input_2)
#     return ev + ew * 10
