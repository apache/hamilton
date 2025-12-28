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
This module defines some feature transformation logic that we'd like to apply.
It then in addition, decorates the functions with @check_output, so that at runtime, we can
execute a validator against the output of the function. The default is to log a warning, unless `importance='fail'`
is specified. In which case, it will halt execution.

Note:
    (1) to handle running on dask, ray, and spark, you will see some `@config.when*` decorators, which will
    determine whether this function should exist or not depending on some configuration passed in.
    (2) instead of @config.when* we could instead move these functions into specific independent modules, and then in
    the driver choose which one to use for the DAG. For the purposes of this example, we decided one file is simpler.
    (3) As of the 1.9.0 release, Hamilton, by default, does not handle data frame validation. Please use the Pandera
    integration - see `examples/data_quality/pandera` for an example.

"""

import numpy as np
import pandas as pd

from hamilton.function_modifiers import check_output, config


@check_output(range=(20.0, 60.0), data_type=np.float64)
def age_mean(age: pd.Series) -> np.float64:
    """Average of age"""
    return age.mean()


@check_output(range=(-120.0, 120.0), data_type=np.float64, allow_nans=False)
def age_zero_mean(age: pd.Series, age_mean: np.float64) -> pd.Series:
    """Zero mean of age"""
    return age - age_mean


@check_output(range=(0.0, 40.0), data_type=np.float64)
def age_std_dev(age: pd.Series) -> np.float64:
    """Standard deviation of age."""
    return age.std()


@check_output(range=(-4.0, 4.0), data_type=np.float64, allow_nans=False)
def age_zero_mean_unit_variance(age_zero_mean: pd.Series, age_std_dev: np.float64) -> pd.Series:
    """Zero mean unit variance value of age"""
    return age_zero_mean / age_std_dev


@config.when_not_in(execution=["spark", "dask"])
def seasons_encoded__base(seasons: pd.Series) -> pd.DataFrame:
    """One hot encodes seasons into 4 dimensions:
    1 - first season
    2 - second season
    3 - third season
    4 - fourth season
    """
    return pd.get_dummies(seasons, prefix="seasons")


@config.when_in(execution=["spark"])
def seasons_encoded__spark(seasons: pd.Series) -> pd.DataFrame:
    """One hot encodes seasons into 4 dimensions:
    1 - first season
    2 - second season
    3 - third season
    4 - fourth season
    """
    import pyspark.pandas as ps

    return ps.get_dummies(seasons, prefix="seasons")


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
    df = dd.get_dummies(categorized, prefix="seasons")
    return df


@check_output(data_type=np.bool_, values_in=[0, 1], allow_nans=False)
def seasons_1(seasons_encoded: pd.DataFrame) -> pd.Series:
    """Returns column seasons_1"""
    return seasons_encoded["seasons_1"]


@check_output(data_type=np.bool_, values_in=[0, 1], allow_nans=False)
def seasons_2(seasons_encoded: pd.DataFrame) -> pd.Series:
    """Returns column seasons_2"""
    return seasons_encoded["seasons_2"]


@check_output(data_type=np.bool_, values_in=[0, 1], allow_nans=False)
def seasons_3(seasons_encoded: pd.DataFrame) -> pd.Series:
    """Returns column seasons_3"""
    return seasons_encoded["seasons_3"]


@check_output(data_type=np.bool_, values_in=[0, 1], allow_nans=False)
def seasons_4(seasons_encoded: pd.DataFrame) -> pd.Series:
    """Returns column seasons_4"""
    return seasons_encoded["seasons_4"]


@config.when_not_in(execution=["spark", "dask"])
def day_of_week_encoded__base(day_of_the_week: pd.Series) -> pd.DataFrame:
    """One hot encodes day of week into five dimensions -- Saturday & Sunday weren't present.
    1 - Sunday, 2 - Monday, 3 - Tuesday, 4 - Wednesday, 5 - Thursday, 6 - Friday, 7 - Saturday.
    """
    return pd.get_dummies(day_of_the_week, prefix="day_of_the_week")


@config.when_in(execution=["spark"])
def day_of_week_encoded__spark(day_of_the_week: pd.Series) -> pd.DataFrame:
    """One hot encodes day of week into five dimensions -- Saturday & Sunday weren't present.
    1 - Sunday, 2 - Monday, 3 - Tuesday, 4 - Wednesday, 5 - Thursday, 6 - Friday, 7 - Saturday.
    """
    import pyspark.pandas as ps

    return ps.get_dummies(day_of_the_week, prefix="day_of_the_week")


@config.when_in(execution=["dask"])
def day_of_week_encoded__dask(day_of_the_week: pd.Series) -> pd.DataFrame:
    """One hot encodes day of week into five dimensions -- Saturday & Sunday weren't present.
    1 - Sunday, 2 - Monday, 3 - Tuesday, 4 - Wednesday, 5 - Thursday, 6 - Friday, 7 - Saturday.
    """
    import dask.dataframe as dd

    categorized = day_of_the_week.astype(str).to_frame().categorize()
    df = dd.get_dummies(categorized, prefix="day_of_the_week")
    return df


@check_output(data_type=np.bool_, values_in=[0, 1], allow_nans=False)
def day_of_the_week_2(day_of_week_encoded: pd.DataFrame) -> pd.Series:
    """Pulls out the day_of_the_week_2 column."""
    return day_of_week_encoded["day_of_the_week_2"]


@check_output(data_type=np.bool_, values_in=[0, 1], allow_nans=False)
def day_of_the_week_3(day_of_week_encoded: pd.DataFrame) -> pd.Series:
    """Pulls out the day_of_the_week_3 column."""
    return day_of_week_encoded["day_of_the_week_3"]


@check_output(data_type=np.bool_, values_in=[0, 1], allow_nans=False)
def day_of_the_week_4(day_of_week_encoded: pd.DataFrame) -> pd.Series:
    """Pulls out the day_of_the_week_4 column."""
    return day_of_week_encoded["day_of_the_week_4"]


@check_output(data_type=np.bool_, values_in=[0, 1], allow_nans=False)
def day_of_the_week_5(day_of_week_encoded: pd.DataFrame) -> pd.Series:
    """Pulls out the day_of_the_week_5 column."""
    return day_of_week_encoded["day_of_the_week_5"]


@check_output(data_type=np.bool_, values_in=[0, 1], allow_nans=False)
def day_of_the_week_6(day_of_week_encoded: pd.DataFrame) -> pd.Series:
    """Pulls out the day_of_the_week_6 column."""
    return day_of_week_encoded["day_of_the_week_6"]


@check_output(data_type=np.int64, values_in=[0, 1], allow_nans=False)
def has_children(son: pd.Series) -> pd.Series:
    """Single variable that says whether someone has any children or not."""
    return (son > 0).astype(int)


@check_output(data_type=np.int64, values_in=[0, 1], allow_nans=False)
def has_pet(pet: pd.Series) -> pd.Series:
    """Single variable that says whether someone has any pets or not."""
    return (pet > 0).astype(int)


@check_output(data_type=np.int64, values_in=[0, 1], allow_nans=False)
def is_summer(month_of_absence: pd.Series) -> pd.Series:
    """Is it summer in Brazil? i.e. months of December, January, February."""
    return month_of_absence.isin([1, 2, 12]).astype(int)
