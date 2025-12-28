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

import gc
import logging
import os
from typing import Dict

import pandas as pd
import utils

from hamilton.function_modifiers import config, extract_columns, extract_fields

logger = logging.getLogger(__name__)


def _load_csv(
    path: str, name: str, verbose: bool = True, reduce_memory: bool = True
) -> pd.DataFrame:
    """Helper function to load csv files.

    Given that loading from parquet is faster than csv, this function will also save a parquet version of the csv file.

    :param path:
    :param name:
    :param verbose:
    :param reduce_memory:
    :return:
    """
    parquet_path = path.replace(".csv", ".parquet")
    if os.path.exists(parquet_path):
        logger.info("Loading from parquet.")
        data_frame = pd.read_parquet(parquet_path)
    else:
        data_frame = pd.read_csv(path)
        data_frame.to_parquet(parquet_path)
    if reduce_memory:
        data_frame = utils.reduce_mem_usage(data_frame, name, verbose=verbose)
    if verbose:
        logger.info(
            "{} has {} rows and {} columns".format(name, data_frame.shape[0], data_frame.shape[1])
        )
    return data_frame


def calendar(
    calendar_path: str = "/kaggle/input/m5-forecasting-accuracy/calendar.csv",
) -> pd.DataFrame:
    """Loads the calendar data.

    Performs some normalization on it.

    :param calendar_path:
    :return:
    """
    _calendar = _load_csv(calendar_path, "calendar", True, True)
    # drop some calendar features -- TBD whether this is the best place
    _calendar.drop(["weekday", "wday", "month", "year"], inplace=True, axis=1)
    nan_features = ["event_name_1", "event_type_1", "event_name_2", "event_type_2"]
    for feature in nan_features:
        _calendar[feature].fillna("unknown", inplace=True)
    _calendar["date"] = pd.to_datetime(_calendar["date"])
    return _calendar


def sell_prices(
    sell_prices_path: str = "/kaggle/input/m5-forecasting-accuracy/sell_prices.csv",
) -> pd.DataFrame:
    """Loads the sell prices data.

    :param sell_prices_path:
    :return:
    """
    _sell_prices = _load_csv(sell_prices_path, "sell_prices", True, True)
    return _sell_prices


def sales_train_validation(
    sales_train_validation_path: str = "/kaggle/input/m5-forecasting-accuracy/sales_train_validation.csv",
) -> pd.DataFrame:
    """Loads the sales train validation data.

    Makes the data into a shape we want to work with.
    :param sales_train_validation_path:
    :return:
    """
    _sales_train_validation = _load_csv(
        sales_train_validation_path, "sales_train_validation", True, reduce_memory=False
    )
    _sales_train_validation = pd.melt(
        _sales_train_validation,
        id_vars=["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"],
        var_name="day",
        value_name="demand",
    )
    _sales_train_validation = utils.reduce_mem_usage(
        _sales_train_validation, "sales_train_validation", verbose=True
    )
    logger.info(
        "Melted sales train validation has {} rows and {} columns".format(
            _sales_train_validation.shape[0], _sales_train_validation.shape[1]
        )
    )
    _sales_train_validation["part"] = "train"
    return _sales_train_validation


@extract_fields(
    {"test1_base": pd.DataFrame, "test2_base": pd.DataFrame, "submission": pd.DataFrame}
)
def submission_loader(
    submission_path: str = "/kaggle/input/m5-forecasting-accuracy/sample_submission.csv",
) -> Dict[str, pd.DataFrame]:
    """Loads the submission data.

    The notebook I got this from did some weird splitting with test1 and test 2.
    I'm not sure why they did that, but I replicated that logic here anyway.

    :param submission_path:
    :return: dict of dataframes
    """
    submission = _load_csv(submission_path, "submission", True, reduce_memory=False)
    # seperate test dataframes
    test1_rows = [row for row in submission["id"] if "validation" in row]
    test2_rows = [row for row in submission["id"] if "evaluation" in row]
    test1 = submission[submission["id"].isin(test1_rows)]
    test2 = submission[submission["id"].isin(test2_rows)]

    # change column names
    test1.columns = [
        "id",
        "d_1914",
        "d_1915",
        "d_1916",
        "d_1917",
        "d_1918",
        "d_1919",
        "d_1920",
        "d_1921",
        "d_1922",
        "d_1923",
        "d_1924",
        "d_1925",
        "d_1926",
        "d_1927",
        "d_1928",
        "d_1929",
        "d_1930",
        "d_1931",
        "d_1932",
        "d_1933",
        "d_1934",
        "d_1935",
        "d_1936",
        "d_1937",
        "d_1938",
        "d_1939",
        "d_1940",
        "d_1941",
    ]
    test2.columns = [
        "id",
        "d_1942",
        "d_1943",
        "d_1944",
        "d_1945",
        "d_1946",
        "d_1947",
        "d_1948",
        "d_1949",
        "d_1950",
        "d_1951",
        "d_1952",
        "d_1953",
        "d_1954",
        "d_1955",
        "d_1956",
        "d_1957",
        "d_1958",
        "d_1959",
        "d_1960",
        "d_1961",
        "d_1962",
        "d_1963",
        "d_1964",
        "d_1965",
        "d_1966",
        "d_1967",
        "d_1968",
        "d_1969",
    ]

    return {"test1_base": test1, "test2_base": test2, "submission": submission}


def product(sales_train_validation: pd.DataFrame) -> pd.DataFrame:
    """Creates a "product" table from the sales train validation data.

    :param sales_train_validation:
    :return:
    """
    # get product table
    _product = sales_train_validation[
        ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]
    ].drop_duplicates()
    return _product


def _merge_test_set_with_product(
    base_df: pd.DataFrame, product: pd.DataFrame, part_value: str
) -> pd.DataFrame:
    """Helper function to merge the test set with the product table.

    :param base_df:
    :param product:
    :param part_value:
    :return:
    """
    merged_df = base_df.merge(product, how="left", on="id")
    merged_df = pd.melt(
        merged_df,
        id_vars=["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"],
        var_name="day",
        value_name="demand",
    )
    merged_df["part"] = part_value
    return merged_df


@config.when(load_test2="True")
def base_dataset__full(
    test1_base: pd.DataFrame,
    test2_base: pd.DataFrame,
    product: pd.DataFrame,
    sales_train_validation: pd.DataFrame,
) -> pd.DataFrame:
    """Creates the base dataset we're building from.

    This is only invoked if you're wanting test2 to be used as well.

    :param test1_base:
    :param test2_base:
    :param product:
    :param sales_train_validation:
    :return:
    """
    # create test1 and test2
    test1 = _merge_test_set_with_product(test1_base, product, "test1")
    test2 = _merge_test_set_with_product(test2_base, product, "test2")
    data = pd.concat([sales_train_validation, test1, test2], axis=0)
    return data


@config.when(load_test2="False")
def base_dataset__test1_only(
    test1_base: pd.DataFrame, product: pd.DataFrame, sales_train_validation: pd.DataFrame
) -> pd.DataFrame:
    """Creates the base dataset we're building from.

    This is the default one.

    :param test1_base:
    :param product:
    :param sales_train_validation:
    :return:
    """
    # create test1 only
    test1 = _merge_test_set_with_product(test1_base, product, "test1")
    data = pd.concat([sales_train_validation, test1], axis=0)
    return data


@extract_columns(
    *[
        "id",
        "item_id",
        "dept_id",
        "cat_id",
        "store_id",
        "state_id",
        "demand",
        "part",
        "date",
        "wm_yr_wk",
        "event_name_1",
        "event_type_1",
        "event_name_2",
        "event_type_2",
        "snap_CA",
        "snap_TX",
        "snap_WI",
        "sell_price",
    ]
)
def base_training_data(
    base_dataset: pd.DataFrame,
    calendar: pd.DataFrame,
    sell_prices: pd.DataFrame,
    num_rows_to_skip: int = 55000000,
) -> pd.DataFrame:
    """Creates the base training data set.

    :param base_dataset:
    :param calendar:
    :param sell_prices:
    :param num_rows_to_skip: how many rows to skip. If zero, or negative, use all rows.
    :return:
    """
    subset = base_dataset.loc[num_rows_to_skip:]
    # notebook crash with the entire dataset (maybee use tensorflow, dask, pyspark xD)
    subset = pd.merge(subset, calendar, how="left", left_on=["day"], right_on=["d"])
    subset.drop(["d", "day"], inplace=True, axis=1)
    # get the sell price data (this feature should be very important)
    subset = subset.merge(sell_prices, on=["store_id", "item_id", "wm_yr_wk"], how="left")
    subset.index = subset.id
    logger.info(
        "Our final dataset to train has {} rows and {} columns".format(
            subset.shape[0], subset.shape[1]
        )
    )
    gc.collect()
    return subset
