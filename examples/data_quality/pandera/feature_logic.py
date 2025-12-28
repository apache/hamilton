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
This modules shows how to use @check_output with Pandera (https://pandera.readthedocs.io/).

It's purpose is to define some feature transformation logic that we'd like to apply.

For runtime data quality checks to happen, we decorate the functions with @check_output. This executes a validator
against the output of the function. The default is to log a warning if validation fails, unless `importance='fail'`
is specified. In which case, it will halt execution.

Note:
    (1) The functions written here scale to running on dask and ray. For spark see `feature_logic_spark.py`.
    (2) Pandera only supports dataframes and series checks. Scalars outputs have to use the standard Hamilton validators.
    (3) If you aren't familiar with Pandera we invite you to look at
    https://pandera.readthedocs.io/en/stable/reference/generated/pandera.checks.Check.html# specifically the "Methods"
    section. That will show you what other checks Pandera comes with.
    (4) If you require dataframe validation - see the examples here.

"""

import numpy as np
import pandas as pd
import pandera as pa

from hamilton.function_modifiers import check_output, config


# pandera doesn't operate over single values
@check_output(range=(20.0, 60.0), data_type=np.float64)
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
@check_output(range=(0.0, 40.0), data_type=np.float64)
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
        "seasons_1": pa.Column(np.uint8, checks=[pa.Check.isin([0, 1])], nullable=False),
        "seasons_2": pa.Column(np.uint8, checks=[pa.Check.isin([0, 1])], nullable=False),
        "seasons_3": pa.Column(np.uint8, checks=[pa.Check.isin([0, 1])], nullable=False),
        "seasons_4": pa.Column(np.uint8, checks=[pa.Check.isin([0, 1])], nullable=False),
    },
    strict=True,
)


@check_output(schema=seasons_encoded_schema)
@config.when_not_in(execution=["dask"])
def seasons_encoded__base(seasons: pd.Series) -> pd.DataFrame:
    """One hot encodes seasons into 4 dimensions:
    1 - first season
    2 - second season
    3 - third season
    4 - fourth season
    """
    return pd.get_dummies(seasons, prefix="seasons", dtype=np.uint8)


@check_output(schema=seasons_encoded_schema)
@config.when_in(execution=["dask"])
def seasons_encoded__dask(seasons: pd.Series) -> pd.DataFrame:
    """One hot encodes seasons into 4 dimensions:
    1 - first season
    2 - second season
    3 - third season
    4 - fourth season
    """
    import dask.dataframe as dd

    categorized = seasons.astype(str).to_frame().categorize()
    df = dd.get_dummies(categorized, prefix="seasons", dtype=np.uint8)
    return df


seasons_schema = pa.SeriesSchema(
    np.uint8,
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
        "day_of_the_week_2": pa.Column(np.uint8, checks=[pa.Check.isin([0, 1])], nullable=False),
        "day_of_the_week_3": pa.Column(np.uint8, checks=[pa.Check.isin([0, 1])], nullable=False),
        "day_of_the_week_4": pa.Column(np.uint8, checks=[pa.Check.isin([0, 1])], nullable=False),
        "day_of_the_week_5": pa.Column(np.uint8, checks=[pa.Check.isin([0, 1])], nullable=False),
        "day_of_the_week_6": pa.Column(np.uint8, checks=[pa.Check.isin([0, 1])], nullable=False),
    },
    strict=True,
)


@check_output(schema=day_of_week_encoded_schema)
@config.when_not_in(execution=["dask"])
def day_of_week_encoded__base(day_of_the_week: pd.Series) -> pd.DataFrame:
    """One hot encodes day of week into five dimensions -- Saturday & Sunday weren't present.
    1 - Sunday, 2 - Monday, 3 - Tuesday, 4 - Wednesday, 5 - Thursday, 6 - Friday, 7 - Saturday.
    """
    return pd.get_dummies(day_of_the_week, prefix="day_of_the_week", dtype=np.uint8)


@check_output(schema=day_of_week_encoded_schema)
@config.when_in(execution=["dask"])
def day_of_week_encoded__dask(day_of_the_week: pd.Series) -> pd.DataFrame:
    """One hot encodes day of week into five dimensions -- Saturday & Sunday weren't present.
    1 - Sunday, 2 - Monday, 3 - Tuesday, 4 - Wednesday, 5 - Thursday, 6 - Friday, 7 - Saturday.
    """
    import dask.dataframe as dd

    categorized = day_of_the_week.astype(str).to_frame().categorize()
    df = dd.get_dummies(categorized, prefix="day_of_the_week", dtype=np.uint8)
    return df


day_of_week_schema = pa.SeriesSchema(
    np.uint8,
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
