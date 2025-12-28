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

from hamilton.function_modifiers import extract_columns


def with_flags(
    avatarId: pd.Series, darkshore_flag: pd.Series, durotar_flag: pd.Series
) -> pd.DataFrame:
    _df = pd.concat([avatarId, darkshore_flag, durotar_flag], axis=1)
    _df.columns = ["avatarId", "darkshore_flag", "durotar_flag"]
    return _df


@extract_columns("total_count", "darkshore_count", "durotar_count")
def zone_counts(with_flags: pd.DataFrame, aggregation_level: str) -> pd.DataFrame:
    return with_flags.groupby(aggregation_level).agg(
        total_count=("darkshore_flag", "count"),
        darkshore_count=("darkshore_flag", "sum"),
        durotar_count=("durotar_flag", "sum"),
    )
