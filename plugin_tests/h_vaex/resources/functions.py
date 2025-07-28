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

import numpy as np
import pandas as pd
import vaex

from hamilton.function_modifiers import extract_columns


@extract_columns("a", "b")
def generate_df() -> vaex.dataframe.DataFrame:
    return vaex.from_pandas(pd.DataFrame({"a": [1, 2, 3], "b": [2, 3, 4]}))


def a_plus_b_expression(
    a: vaex.expression.Expression, b: vaex.expression.Expression
) -> vaex.expression.Expression:
    return a + b


def a_plus_b_nparray(a: vaex.expression.Expression, b: vaex.expression.Expression) -> np.ndarray:
    return (a + b).to_numpy()


def a_mean(a: vaex.expression.Expression) -> float:
    return a.mean()


def b_mean(b: vaex.expression.Expression) -> float:
    return b.mean()


def ab_as_df(
    a: vaex.expression.Expression, b: vaex.expression.Expression
) -> vaex.dataframe.DataFrame:
    return vaex.from_pandas(pd.DataFrame({"a_in_df": a.to_numpy(), "b_in_df": b.to_numpy()}))
