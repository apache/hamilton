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

from hamilton.function_modifiers import load_from, value


@load_from.csv(path=value("test_data/marketing_spend.csv"))
def spend(data: pd.DataFrame) -> pd.DataFrame:
    """Takes in the dataframe and then generates a date index column to it,
    where each row is a day starting from 2020-01-01"""
    data["date"] = pd.date_range(start="2020-01-01", periods=len(data), freq="D")
    return data


@load_from.csv(path=value("test_data/churn.csv"))
def churn(data: pd.DataFrame) -> pd.DataFrame:
    """Takes in the dataframe and then generates a date index column to it,
    where each row is a day starting from 2020-01-01
    """
    data["date"] = pd.date_range(start="2020-01-01", periods=len(data), freq="D")
    return data


@load_from.csv(path=value("test_data/signups.csv"))
def signups(data: pd.DataFrame) -> pd.DataFrame:
    """Takes in the dataframe and then generates a date index column to it,
    where each row is a day starting from 2020-01-01
    """
    data["date"] = pd.date_range(start="2020-01-01", periods=len(data), freq="D")
    return data
