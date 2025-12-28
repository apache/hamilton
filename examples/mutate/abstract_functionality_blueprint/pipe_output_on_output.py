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

from typing import Dict

from hamilton.function_modifiers import (
    extract_fields,
    hamilton_exclude,
    pipe_output,
    step,
)


@hamilton_exclude
def pre_step(something: int) -> int:
    return something + 10


@hamilton_exclude
def post_step(something: int) -> int:
    return something + 100


@hamilton_exclude
def something_else(something: int) -> int:
    return something + 1000


def a() -> int:
    return 10


@pipe_output(
    step(something_else),  # gets applied to all sink nodes
    step(pre_step).named(name="transform_1").on_output("field_1"),  # only applied to field_1
    step(post_step)
    .named(name="transform_2")
    .on_output(["field_1", "field_3"]),  # applied to field_1 and field_3
)
@extract_fields({"field_1": int, "field_2": int, "field_3": int})
def foo(a: int) -> Dict[str, int]:
    return {"field_1": 1, "field_2": 2, "field_3": 3}
