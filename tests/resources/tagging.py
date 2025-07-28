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

from hamilton.function_modifiers import extract_fields, tag


@tag(test="a")
def a() -> int:
    return 0


@tag(test="b_c")
@extract_fields({"b": int, "c": str})
def b_c(a: int) -> dict:
    return {"b": a, "c": str(a)}


@tag(test_list=["us", "uk"])
def d(a: int) -> int:
    return a
