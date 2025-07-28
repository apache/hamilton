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


def base_func(a: pd.Series, b: pd.Series) -> htypes.column[pd.Series, int]:
    """Pandas UDF function."""
    return a + b


def base_func2(base_func: int, c: int) -> int:
    """Vanilla UDF function. This depends on a pandas UDF function."""
    return base_func + c


def base_func3(c: int, d: int) -> int:
    """This function is not satisfied by the dataframe. So is computed without using
    the columns in the dataframe."""
    return c + d
