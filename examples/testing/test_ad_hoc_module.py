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

"""Testing patterns that don't need a separate module on disk.

Sometimes you want to define a tiny set of functions inside the test itself --
to exercise a custom materializer, a graph adapter, or a regression case --
without creating a whole new ``.py`` file. ``hamilton.ad_hoc_utils`` exposes
``create_temporary_module`` for exactly that.
"""

from hamilton import ad_hoc_utils, driver


def test_temporary_module_can_drive_a_dag() -> None:
    """Define functions inline, package them into a module, run the Driver."""

    def base(value: int) -> int:
        return value + 1

    def squared(base: int) -> int:
        return base * base

    temp_module = ad_hoc_utils.create_temporary_module(base, squared)

    dr = driver.Builder().with_modules(temp_module).build()

    result = dr.execute(["squared"], inputs={"value": 4})

    # base = 4 + 1 = 5; squared = 25
    assert result["squared"] == 25
