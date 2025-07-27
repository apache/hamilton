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

from typing import Any

import numpy as np

from hamilton import registry

try:
    import vaex
except ImportError as e:
    raise NotImplementedError("Vaex is not installed.") from e

DATAFRAME_TYPE = vaex.dataframe.DataFrame
COLUMN_TYPE = vaex.expression.Expression


@registry.get_column.register(vaex.dataframe.DataFrame)
def get_column_vaex(df: vaex.dataframe.DataFrame, column_name: str) -> vaex.expression.Expression:
    return df[column_name]


@registry.fill_with_scalar.register(vaex.dataframe.DataFrame)
def fill_with_scalar_vaex(
    df: vaex.dataframe.DataFrame, column_name: str, scalar_value: Any
) -> vaex.dataframe.DataFrame:
    df[column_name] = np.full((df.shape[0],), scalar_value)
    return df


def register_types():
    """Function to register the types for this extension."""
    registry.register_types("vaex", DATAFRAME_TYPE, COLUMN_TYPE)


register_types()
