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

from typing import List

from hamilton.function_modifiers import config
from hamilton.htypes import Collect, Parallelizable
from hamilton.lifecycle.default import accept_error_sentinels


@config.when(test_front="good")
def input_maker__good(n: int) -> int:
    return n


@config.when(test_front="bad")
def input_maker__bad(n: int) -> int:
    raise Exception("Went wrong")


@config.when(test_state="middle")
def distro__middle(input_maker: int) -> Parallelizable[int]:
    for x in range(input_maker):
        if x > 4:
            raise Exception("bad")
        yield x * 3


@config.when(test_state="early")
def distro__early(input_maker: int) -> Parallelizable[int]:
    raise Exception("bad")
    for x in range(input_maker):
        yield x * 3


@config.when(test_state="pass")
def distro__pass(input_maker: int) -> Parallelizable[int]:
    for x in range(input_maker):
        yield x * 3


def some_math(distro: int) -> float:
    if distro > 15:
        raise Exception("No no no")
    return distro * 2.0


def other_math(distro: int) -> float:
    if distro < 10:
        raise Exception("Not allowed")
    return distro + 1


@accept_error_sentinels
def gather_math(some_math: float, other_math: float) -> List[float]:
    return [some_math, other_math]


def distro_end(gather_math: Collect[List[float]]) -> List[float]:
    ans = [x for x in gather_math]
    return ans


def distro_gather(some_math: Collect[float]) -> List[float]:
    ans = [x for x in some_math]
    return ans
