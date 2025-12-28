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
We suggest you start by reading `pandera/feature_logic.py` before looking at this file.

This module is practically identical to `pandera/feature_logic.py` except for the following:

1. There is no @config use -- instead this assumes that this file will ONLY BE USED in a spark context.
   E.g. `import pyspark.pandas as ps` is top level.
2. The data type checks on the output of functions are different. E.g. float vs np.float64. Execution on spark
   results in different data types.
"""

import numpy as np
import pandas as pd
import pandera as pa
import pyspark.pandas as ps

from hamilton.function_modifiers import check_output


# pandera doesn't operate over single values
@check_output(range=(20.0, 60.0), data_type=float)
def age_mean(age: pd.Series) -> np.float64:
    """Average of age"""
    return age.mean()


age_zero_mean_schema = pa.SeriesSchema(
    float,
    checks=[
        pa.Check.in_range(-120.0, 120.0),
    ],
    nullable=False,
)


@check_output(schema=age_zero_mean_schema)
def age_zero_mean(age: pd.Series, age_mean: np.float64) -> pd.Series:
    """Zero mean of age"""
    return age - age_mean


age_std_dev_schema = pa.SeriesSchema(
    float,
    checks=[
        pa.Check.in_range(0.0, 40.0),
    ],
)


# pandera doesn't operate over single values
@check_output(range=(0.0, 40.0), data_type=float)
def age_std_dev(age: pd.Series) -> np.float64:
    """Standard deviation of age."""
    return age.std()


age_zero_mean_unit_variance_schema = pa.SeriesSchema(
    float,
    checks=[
        pa.Check.in_range(-4.0, 4.0),
    ],
    nullable=False,
)


@check_output(schema=age_zero_mean_unit_variance_schema)
def age_zero_mean_unit_variance(age_zero_mean: pd.Series, age_std_dev: np.float64) -> pd.Series:
    """Zero mean unit variance value of age"""
    return age_zero_mean / age_std_dev


seasons_encoded_schema = pa.DataFrameSchema(
    {
        "seasons_1": pa.Column(np.int8, checks=[pa.Check.isin([0, 1])], nullable=False),
        "seasons_2": pa.Column(np.int8, checks=[pa.Check.isin([0, 1])], nullable=False),
        "seasons_3": pa.Column(np.int8, checks=[pa.Check.isin([0, 1])], nullable=False),
        "seasons_4": pa.Column(np.int8, checks=[pa.Check.isin([0, 1])], nullable=False),
    },
    strict=True,
)


@check_output(schema=seasons_encoded_schema)
def seasons_encoded(seasons: pd.Series) -> pd.DataFrame:
    """One hot encodes seasons into 4 dimensions:
    1 - first season
    2 - second season
    3 - third season
    4 - fourth season
    """
    return ps.get_dummies(seasons, prefix="seasons", dtype=np.uint8)


seasons_schema = pa.SeriesSchema(
    np.int8,
    checks=[
        pa.Check.isin([0, 1]),
    ],
    nullable=False,
)


@check_output(schema=seasons_schema)
def seasons_1(seasons_encoded: pd.DataFrame) -> pd.Series:
    """Returns column seasons_1"""
    return seasons_encoded["seasons_1"]


@check_output(schema=seasons_schema)
def seasons_2(seasons_encoded: pd.DataFrame) -> pd.Series:
    """Returns column seasons_2"""
    return seasons_encoded["seasons_2"]


@check_output(schema=seasons_schema)
def seasons_3(seasons_encoded: pd.DataFrame) -> pd.Series:
    """Returns column seasons_3"""
    return seasons_encoded["seasons_3"]


@check_output(schema=seasons_schema)
def seasons_4(seasons_encoded: pd.DataFrame) -> pd.Series:
    """Returns column seasons_4"""
    return seasons_encoded["seasons_4"]


day_of_week_encoded_schema = pa.DataFrameSchema(
    {
        "day_of_the_week_2": pa.Column(np.int8, checks=[pa.Check.isin([0, 1])], nullable=False),
        "day_of_the_week_3": pa.Column(np.int8, checks=[pa.Check.isin([0, 1])], nullable=False),
        "day_of_the_week_4": pa.Column(np.int8, checks=[pa.Check.isin([0, 1])], nullable=False),
        "day_of_the_week_5": pa.Column(np.int8, checks=[pa.Check.isin([0, 1])], nullable=False),
        "day_of_the_week_6": pa.Column(np.int8, checks=[pa.Check.isin([0, 1])], nullable=False),
    },
    strict=True,
)


@check_output(schema=day_of_week_encoded_schema)
def day_of_week_encoded(day_of_the_week: pd.Series) -> pd.DataFrame:
    """One hot encodes day of week into five dimensions -- Saturday & Sunday weren't present.
    1 - Sunday, 2 - Monday, 3 - Tuesday, 4 - Wednesday, 5 - Thursday, 6 - Friday, 7 - Saturday.
    """
    return ps.get_dummies(day_of_the_week, prefix="day_of_the_week", dtype=np.uint8)


day_of_week_schema = pa.SeriesSchema(
    np.int8,
    checks=[
        pa.Check.isin([0, 1]),
    ],
    nullable=False,
)


@check_output(schema=day_of_week_schema)
def day_of_the_week_2(day_of_week_encoded: pd.DataFrame) -> pd.Series:
    """Pulls out the day_of_the_week_2 column."""
    return day_of_week_encoded["day_of_the_week_2"]


@check_output(schema=day_of_week_schema)
def day_of_the_week_3(day_of_week_encoded: pd.DataFrame) -> pd.Series:
    """Pulls out the day_of_the_week_3 column."""
    return day_of_week_encoded["day_of_the_week_3"]


@check_output(schema=day_of_week_schema)
def day_of_the_week_4(day_of_week_encoded: pd.DataFrame) -> pd.Series:
    """Pulls out the day_of_the_week_4 column."""
    return day_of_week_encoded["day_of_the_week_4"]


@check_output(schema=day_of_week_schema)
def day_of_the_week_5(day_of_week_encoded: pd.DataFrame) -> pd.Series:
    """Pulls out the day_of_the_week_5 column."""
    return day_of_week_encoded["day_of_the_week_5"]


@check_output(schema=day_of_week_schema)
def day_of_the_week_6(day_of_week_encoded: pd.DataFrame) -> pd.Series:
    """Pulls out the day_of_the_week_6 column."""
    return day_of_week_encoded["day_of_the_week_6"]


has_children_schema = pa.SeriesSchema(
    int,
    checks=[
        pa.Check.isin([0, 1]),
    ],
    nullable=False,
)


@check_output(schema=has_children_schema)
def has_children(son: pd.Series) -> pd.Series:
    """Single variable that says whether someone has any children or not."""
    return (son > 0).astype(int)


has_pet_schema = pa.SeriesSchema(
    int,
    checks=[
        pa.Check.isin([0, 1]),
    ],
    nullable=False,
)


@check_output(schema=has_pet_schema)
def has_pet(pet: pd.Series) -> pd.Series:
    """Single variable that says whether someone has any pets or not."""
    return (pet > 0).astype(int)


is_summer_schema = pa.SeriesSchema(
    int,
    checks=[
        pa.Check.isin([0, 1]),
    ],
    nullable=False,
)


@check_output(schema=is_summer_schema)
def is_summer(month_of_absence: pd.Series) -> pd.Series:
    """Is it summer in Brazil? i.e. months of December, January, February."""
    return month_of_absence.isin([1, 2, 12]).astype(int)
