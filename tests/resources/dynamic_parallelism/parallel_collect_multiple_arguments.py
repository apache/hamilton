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

import collections
import functools

from hamilton.htypes import Collect, Parallelizable

_fn_call_counter = collections.Counter()


def _track_fn_call(fn) -> callable:
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        _fn_call_counter[fn.__name__] += 1
        return fn(*args, **kwargs)

    return wrapped


def _reset_counter():
    _fn_call_counter.clear()


@_track_fn_call
def not_to_repeat() -> int:
    return -1


@_track_fn_call
def number_to_repeat(iterations: int) -> Parallelizable[int]:
    for i in range(iterations):
        yield i


@_track_fn_call
def something_else_not_to_repeat() -> int:
    return -2


@_track_fn_call
def double(number_to_repeat: int) -> int:
    return number_to_repeat * 2


@_track_fn_call
def summed(double: Collect[int], not_to_repeat: int, something_else_not_to_repeat: int) -> int:
    return sum(double) + not_to_repeat + something_else_not_to_repeat
