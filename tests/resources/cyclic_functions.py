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
Module for cyclic functions to test graph things with.
"""

# we import this to check we don't pull in this function when parsing this module.
from tests.resources import only_import_me  # noqa: F401


def A(b: int, c: int) -> int:
    """Function that should become part of the graph - A"""
    return b + c


def B(A: int, D: int) -> int:
    """Function that should become part of the graph - B"""
    return A * A + D


def C(B: int) -> int:  # empty string doc on purpose.
    return B * 2


def D(C: int) -> int:
    return C + 1
