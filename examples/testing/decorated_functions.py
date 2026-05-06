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

"""Functions that use Hamilton decorators.

Decorators are a common source of confusion when testing. The point of this
module is to show that decorators do not get in the way of unit testing -- the
function below the decorator is still a plain Python callable, so you can call
it directly from a test. To test what the decorator *expands to*, drive the
function through a Driver instead (see ``test_decorated_functions.py``).
"""

import pandas as pd

from hamilton.function_modifiers import extract_columns, parameterize, source, tag, value


@tag(owner="growth-team", pii="false")
def total_signups(signups: pd.Series) -> int:
    """Sum of signups across the time window."""
    return int(signups.sum())


@parameterize(
    spend_in_thousands={"raw_value": source("spend"), "divisor": value(1000.0)},
    signups_in_hundreds={"raw_value": source("signups"), "divisor": value(100.0)},
)
def scaled(raw_value: pd.Series, divisor: float) -> pd.Series:
    """Scale a series by a constant divisor.

    `@parameterize` produces one node per entry above. The function itself is
    still a normal callable, so a unit test can call ``scaled(some_series, 1000)``
    directly without a Driver.
    """
    return raw_value / divisor


@extract_columns("scaled_spend", "scaled_signups")
def scaled_features(spend_in_thousands: pd.Series, signups_in_hundreds: pd.Series) -> pd.DataFrame:
    """Bundle the two scaled series into a frame, then expose each column as a node."""
    return pd.DataFrame({"scaled_spend": spend_in_thousands, "scaled_signups": signups_in_hundreds})
