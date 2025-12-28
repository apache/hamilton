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

from hamilton import htypes


def durotar_flag(zone: pd.Series) -> htypes.column[pd.Series, int]:
    return pd.Series((zone == " Durotar").astype(int), index=zone.index)


def darkshore_flag(zone: pd.Series) -> htypes.column[pd.Series, int]:
    return pd.Series((zone == " Darkshore").astype(int), index=zone.index)


def durotar_likelihood(
    durotar_count: pd.Series, total_count: pd.Series
) -> htypes.column[pd.Series, float]:
    return durotar_count / total_count


def darkshore_likelihood(
    darkshore_count: pd.Series, total_count: pd.Series
) -> htypes.column[pd.Series, float]:
    return darkshore_count / total_count
