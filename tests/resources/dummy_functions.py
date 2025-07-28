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
Module for dummy functions to test graph things with.
"""

# we import this to check we don't pull in this function when parsing this module.
from tests.resources import only_import_me


def A(b: int, c: int) -> int:
    """Function that should become part of the graph - A"""
    return b + c


def _do_not_import_me(some_input: int, some_input2: int) -> int:
    """Function that should not become part of the graph - _do_not_import_me."""
    only_import_me.this_is_not_something_we_should_import()
    return some_input + some_input2


def B(A: int) -> int:
    """Function that should become part of the graph - B"""
    return A * A


def C(A: int) -> int:  # empty string doc on purpose.
    return A * 2
