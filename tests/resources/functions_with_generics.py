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

"""
Module for functions with genercis to test graph things with.
"""

from collections.abc import Mapping


def A(b: dict, c: int) -> tuple[dict, int]:
    """Function that should become part of the graph - A"""
    return b, c


def B(A: tuple[dict, int]) -> list:
    """Function that should become part of the graph - B"""
    return [A, A]


def C(B: list) -> dict:
    return {"foo": B}


def D(C: Mapping) -> float:
    return 1.0
