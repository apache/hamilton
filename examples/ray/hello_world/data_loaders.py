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


def spend(spend_location: str) -> pd.Series:
    """Dummy function showing how to wire through loading data.

    :param spend_location:
    :return:
    """
    return pd.Series([10, 10, 20, 40, 40, 50])


def signups(signups_location: str) -> pd.Series:
    """Dummy function showing how to wire through loading data.

    :param signups_location:
    :return:
    """
    return pd.Series([1, 10, 50, 100, 200, 400])
