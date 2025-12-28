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

"""
Module to transform iris data into features.
"""

import numpy as np
import pandas as pd

from hamilton.function_modifiers import parameterize_sources

RAW_FEATURES = ["sepal_length_cm", "sepal_width_cm", "petal_length_cm", "petal_width_cm"]

# Here is more terse code that does the same thing as the below *_log functions.
# Any `@parameterize*` decorator is just a less verbose way of defining functions that differ
# slightly. We don't see anything wrong with verbose code - so we recommend err'ing on the side of
# verbosity, but otherwise for this example show the terser code.
# @parameterize_sources(**{f"{col}_log": {"col": col} for col in RAW_FEATURES})
# def log_value(col: pd.Series) -> pd.Series:
#     """Log value of {col}."""
#     return np.log(col)


def sepal_length_cm_log(sepal_length_cm: pd.Series) -> pd.Series:
    """Log value of sepal_length_cm_."""
    return np.log(sepal_length_cm)


def sepal_width_cm_log(sepal_width_cm: pd.Series) -> pd.Series:
    """Log value of sepal_width_cm_."""
    return np.log(sepal_width_cm)


def petal_length_cm_log(petal_length_cm: pd.Series) -> pd.Series:
    """Log value of petal_length_cm_."""
    return np.log(petal_length_cm)


def petal_width_cm_log(petal_width_cm: pd.Series) -> pd.Series:
    """Log value of petal_width_cm_."""
    return np.log(petal_width_cm)


@parameterize_sources(**{f"{col}_mean": {"col": col} for col in RAW_FEATURES})
def mean_value(col: pd.Series) -> float:
    """Mean of {col}."""
    return col.mean()


@parameterize_sources(**{f"{col}_std": {"col": col} for col in RAW_FEATURES})
def std_value(col: pd.Series) -> float:
    """Standard deviation of {col}."""
    return col.std()


@parameterize_sources(
    **{
        f"{col}_normalized": {"col": col, "col_mean": f"{col}_mean", "col_std": f"{col}_std"}
        for col in RAW_FEATURES
    }
)
def normalized_value(col: pd.Series, col_mean: float, col_std: float) -> pd.Series:
    """Normalized column of {col}."""
    return (col - col_mean) / col_std


def data_set_v1(
    sepal_length_cm_normalized: pd.Series,
    sepal_width_cm_normalized: pd.Series,
    petal_length_cm_normalized: pd.Series,
    petal_width_cm_normalized: pd.Series,
    target_class: pd.Series,
) -> pd.DataFrame:
    """Explicitly define the feature set we want to use."""
    return pd.DataFrame(
        {
            "sepal_length_cm_normalized": sepal_length_cm_normalized,
            "sepal_width_cm_normalized": sepal_width_cm_normalized,
            "petal_length_cm_normalized": petal_length_cm_normalized,
            "petal_width_cm_normalized": petal_width_cm_normalized,
            "target_class": target_class,
        }
    )


def data_set_v2(
    sepal_length_cm_normalized: pd.Series,
    sepal_width_cm_normalized: pd.Series,
    petal_length_cm_normalized: pd.Series,
    petal_width_cm_normalized: pd.Series,
    sepal_length_cm_log: pd.Series,
    sepal_width_cm_log: pd.Series,
    petal_length_cm_log: pd.Series,
    petal_width_cm_log: pd.Series,
    target_class: pd.Series,
) -> pd.DataFrame:
    """Explicitly define the feature set we want to use. This one adds `log` features."""
    return pd.DataFrame(
        {
            "sepal_length_cm_normalized": sepal_length_cm_normalized,
            "sepal_width_cm_normalized": sepal_width_cm_normalized,
            "petal_length_cm_normalized": petal_length_cm_normalized,
            "petal_width_cm_normalized": petal_width_cm_normalized,
            "sepal_length_cm_log": sepal_length_cm_log,
            "sepal_width_cm_log": sepal_width_cm_log,
            "petal_length_cm_log": petal_length_cm_log,
            "petal_width_cm_log": petal_width_cm_log,
            "target_class": target_class,
        }
    )
