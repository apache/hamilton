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
Here are some features that are based on the absenteeism data set.
They are just supposed to be illustrative of the kind of features one might have.

Note (1): we use check_output to warn us if the output is not what we expect; this is
used in both the offline ETL and the online webservice. Use `check_output` to help
encode your expectations about the output of your functions and catch bugs early!

Note (2): we use @config to remove age_mean and age_std_dev from being computed in the online context.
This means they need to be satisfied by either being passed in, or having another module define them.
We do the latter for this example, but having online_loader define them.
"""

import pandas as pd
import pandera as pa

from hamilton.function_modifiers import check_output, config, extract_columns


@check_output(range=(20.0, 60.0), data_type=float)
@config.when_not_in(execution_mode=["online"])
def age_mean(age: pd.Series) -> float:
    """Average of age -- this is not included when execution_mode is "online"."""
    return age.mean()


age_zero_mean_schema = pa.SeriesSchema(
    float,
    checks=[
        pa.Check.in_range(-120.0, 120.0),
    ],
    nullable=False,
)


@check_output(schema=age_zero_mean_schema)
def age_zero_mean(age: pd.Series, age_mean: float) -> pd.Series:
    """Zero mean of age"""
    return age - age_mean


age_std_dev_schema = pa.SeriesSchema(
    float,
    checks=[
        pa.Check.in_range(0.0, 40.0),
    ],
)


@check_output(range=(0.0, 40.0), data_type=float)
@config.when_not_in(execution_mode=["online"])
def age_std_dev(age: pd.Series) -> float:
    """Standard deviation of age -- this is not included when execution_mode is "online"."""
    return age.std()


age_zero_mean_unit_variance_schema = pa.SeriesSchema(
    float,
    checks=[
        pa.Check.in_range(-4.0, 4.0),
    ],
    nullable=False,
)


@check_output(schema=age_zero_mean_unit_variance_schema)
def age_zero_mean_unit_variance(age_zero_mean: pd.Series, age_std_dev: float) -> pd.Series:
    """Zero mean unit variance value of age"""
    return age_zero_mean / age_std_dev


@extract_columns("seasons_1", "seasons_2", "seasons_3", "seasons_4", fill_with=0)
def seasons_encoded(seasons: pd.Series) -> pd.DataFrame:
    """One hot encodes seasons into 4 dimensions:
    1 - first season
    2 - second season
    3 - third season
    4 - fourth season
    """
    return pd.get_dummies(seasons, prefix="seasons")


@extract_columns(
    "day_of_the_week_2",
    "day_of_the_week_3",
    "day_of_the_week_4",
    "day_of_the_week_5",
    "day_of_the_week_6",
    fill_with=0,
)
def day_of_week_encoded(day_of_the_week: pd.Series) -> pd.DataFrame:
    """One hot encodes day of week into five dimensions -- Saturday & Sunday weren't present.
    1 - Sunday, 2 - Monday, 3 - Tuesday, 4 - Wednesday, 5 - Thursday, 6 - Friday, 7 - Saturday.
    """
    return pd.get_dummies(day_of_the_week, prefix="day_of_the_week")


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
