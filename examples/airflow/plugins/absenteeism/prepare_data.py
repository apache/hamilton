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

from typing import List

import numpy as np
import pandas as pd

from hamilton.function_modifiers import config, extract_columns

"""Module level constants are convenient when you want your Hamilton driver to
produce a list of outputs. For example, you can do:

```
import hamilton
import prepare_data

dr = hamilton.driver.Driver({}, prepare_data)
outputs = dr.execute(final_vars=prepare_data.ALL_FEATURES)
```
"""
SOURCE_COLUMNS = [
    "id",
    "reason_for_absence",
    "month_of_absence",
    "day_of_the_week",
    "seasons",
    "transportation_expense",
    "distance_from_residence_to_work",
    "service_time",
    "age",
    "work_load_average_per_day",
    "hit_target",
    "disciplinary_failure",
    "education",
    "son",
    "social_drinker",
    "social_smoker",
    "pet",
    "weight",
    "height",
    "body_mass_index",
    "absenteeism_time_in_hours",
]

ALL_FEATURES = [
    "id",
    "reason_for_absence",
    "distance_from_residence_to_work",
    "service_time",
    "social_drinker",
    "social_smoker",
    "age_zero_mean_unit_variance",
    "has_children",
    "has_pet",
    "is_summer",
    "day_of_the_week_2",
    "day_of_the_week_3",
    "day_of_the_week_4",
    "day_of_the_week_5",
    "day_of_the_week_6",
]


def _rename_columns(columns: List[str]) -> List[str]:
    """convert raw data column names to snakecase and make them compatible
    with Hamilton's naming convention (need to be a valid Python function name)

    NOTE functions prefixed with "_" are not loaded as Hamilton nodes
    """
    return [c.strip().replace("/", "_per_").replace(" ", "_").lower() for c in columns]


@config.when(development_flag=False)
@extract_columns(*SOURCE_COLUMNS)
def sanitized_df__prod(raw_df: pd.DataFrame) -> pd.DataFrame:
    """convert raw data column names to snakecase and make them compatible
    with Hamilton's naming convention (need to be a valid Python function name)

    NOTE config when is used. Functions with a suffix of "__condition" describe
    alternative of the same Hamilton node
    """
    raw_df.columns = _rename_columns(raw_df.columns)

    return raw_df


@config.when_not(development_flag=False)
@extract_columns(*SOURCE_COLUMNS)
def sanitized_df__dev(raw_df: pd.DataFrame) -> pd.DataFrame:
    """identical to sanitized_df__prod(), but loads only first 20 rows"""
    raw_df.columns = _rename_columns(raw_df.columns)

    return raw_df.head(20)


def age_mean(age: pd.Series) -> np.float64:
    """Average of age"""
    return age.mean()


def age_zero_mean(age: pd.Series, age_mean: np.float64) -> pd.Series:
    """Zero mean of age"""
    return age - age_mean


def age_std_dev(age: pd.Series) -> np.float64:
    """Standard deviation of age."""
    return age.std()


def age_zero_mean_unit_variance(age_zero_mean: pd.Series, age_std_dev: np.float64) -> pd.Series:
    """Zero mean unit variance value of age"""
    return age_zero_mean / age_std_dev


def has_children(son: pd.Series) -> pd.Series:
    """Single variable that says whether someone has any children or not."""
    return (son > 0).astype(int)


def has_pet(pet: pd.Series) -> pd.Series:
    """Single variable that says whether someone has any pets or not."""
    return (pet > 0).astype(int)


def is_summer(month_of_absence: pd.Series) -> pd.Series:
    """Is it summer in Brazil? i.e. months of December, January, February."""
    return month_of_absence.isin([1, 2, 12]).astype(int)


@extract_columns(
    "day_of_the_week_2",
    "day_of_the_week_3",
    "day_of_the_week_4",
    "day_of_the_week_5",
    "day_of_the_week_6",
)
def day_of_week_encoded(day_of_the_week: pd.Series) -> pd.DataFrame:
    """One hot encodes day of week into five dimensions -- Saturday & Sunday weren't present.
    1 - Sunday, 2 - Monday, 3 - Tuesday, 4 - Wednesday, 5 - Thursday, 6 - Friday, 7 - Saturday.

    NOTE it is not equivalent to pandas dt.dayofweek which has Monday as 0 and Sunday as 6
    """
    return pd.get_dummies(day_of_the_week, prefix="day_of_the_week")
