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

from hamilton.function_modifiers import config


def new_param() -> str:
    return "dummy"


@config.when(fn_1_version=0)
def fn() -> str:
    pass


@config.when(fn_1_version=1)
def fn__v1() -> str:
    return "version_1"


@config.when(fn_1_version=2)
def fn__v2(new_param: str) -> str:
    return "version_2"


@config.when(fn_1_version=3, name="fn")
def fn_to_rename() -> str:
    return "version_3"
