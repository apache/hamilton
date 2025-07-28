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

from hamilton.function_modifiers import ResolveAt, extract_columns, parameterize, resolve, source


@extract_columns("a", "b", "c", "d", "e")
def df() -> pd.DataFrame:
    """Produces a dataframe with columns a, b, c, d, e consisting entirely of 1s"""
    return pd.DataFrame(
        {
            "a": [1],
            "b": [1],
            "c": [1],
            "d": [1],
            "e": [1],
        }
    )


@resolve(
    when=ResolveAt.CONFIG_AVAILABLE,
    decorate_with=lambda columns_to_sum_map: parameterize(
        **{
            key: {"col_1": source(value[0]), "col_2": source(value[1])}
            for key, value in columns_to_sum_map.items()
        }
    ),
)
def generic_summation(col_1: pd.Series, col_2: pd.Series) -> pd.Series:
    return col_1 + col_2


# TODO -- add grouping then we can test everything
