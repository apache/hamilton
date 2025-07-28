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

import pytest

from hamilton import driver
from hamilton.lifecycle import default

from tests.resources import mismatched_types


def test_noedge_input_type_checking_without_adapter():
    with pytest.raises(ValueError):
        driver.Builder().with_modules(mismatched_types).build()


def test_noedge_input_type_checking_with_adapter():
    dr = (
        driver.Builder()
        .with_modules(mismatched_types)
        .with_adapters(default.NoEdgeAndInputTypeChecking())
        .build()
    )
    actual = dr.execute(["baz"], inputs={"a": 1.02, "number": "aaasdfdsf"})
    assert actual == {"baz": "1.02 2 aaasdfdsf"}
