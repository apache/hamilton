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

from hamilton.function_modifiers import mutate


def data_1() -> int:
    return 10


@mutate(data_1)
def add_something(user_input: int) -> int:
    return user_input + 100


@mutate(data_1)
def add_something_more(user_input: int) -> int:
    return user_input + 1000


@mutate(data_1)
def add_something(user_input: int) -> int:  # noqa
    return user_input + 100
