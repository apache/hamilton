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

import pandas as pd

from hamilton import driver
from hamilton.plugins.h_slack import SlackNotifier


def test_function() -> pd.DataFrame:
    raise Exception("test exception")
    return pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})


if __name__ == "__main__":
    import __main__

    api_key = "YOUR_API_KEY"
    channel = "YOUR_CHANNEL"
    dr = (
        driver.Builder()
        .with_modules(__main__)
        .with_adapters(SlackNotifier(api_key=api_key, channel=channel))
        .build()
    )
    print(dr.execute(["test_function"]))
