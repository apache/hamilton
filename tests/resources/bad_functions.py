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
Module for more dummy functions to test graph things with.
"""

# we import this to check we don't pull in this function when parsing this module.
from tests.resources import only_import_me  # noqa: F401


def A(b, c) -> int:
    """Should error out because we're missing an annotation"""
    return b + c


def B(b: int, c: int):
    """Should error out because we're missing an annotation"""
    return b + c


def C(b: int) -> dict:
    """Setting up type mismatch."""
    return {"hi": "world"}


def D(C: int) -> int:
    """C is the incorrect type."""
    return int(C["hi"])
