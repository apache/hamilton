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

import logging
import sys
import time
from typing import TYPE_CHECKING

import data_loaders
import model_pipeline
import transforms

from hamilton import driver

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


# this is hard coded here, but it could be passed in, or in some other versioned file.
model_params = {
    "num_leaves": 555,
    "min_child_weight": 0.034,
    "feature_fraction": 0.379,
    "bagging_fraction": 0.418,
    "min_data_in_leaf": 106,
    "objective": "regression",
    "max_depth": -1,
    "learning_rate": 0.005,
    "boosting_type": "gbdt",
    "bagging_seed": 11,
    "metric": "rmse",
    "verbosity": -1,
    "reg_alpha": 0.3899,
    "reg_lambda": 0.648,
    "random_state": 222,
}


def main():
    """The main function to orchestrate everything."""
    start_time = time.time()
    config = {
        "calendar_path": "m5-forecasting-accuracy/calendar.csv",
        "sell_prices_path": "m5-forecasting-accuracy/sell_prices.csv",
        "sales_train_validation_path": "m5-forecasting-accuracy/sales_train_validation.csv",
        "submission_path": "m5-forecasting-accuracy/sample_submission.csv",
        "load_test2": "False",
        "n_fold": 3,
        "model_params": model_params,
        "num_rows_to_skip": 27500000,  # for training set
    }
    dr = driver.Driver(config, data_loaders, transforms, model_pipeline)
    dr.display_all_functions("./all_functions.dot", {"format": "png"})
    dr.visualize_execution(
        ["kaggle_submission_df"], "./kaggle_submission_df.dot", {"format": "png"}
    )
    kaggle_submission_df: pd.DataFrame = dr.execute(["kaggle_submission_df"])
    duration = time.time() - start_time
    logger.info(f"Duration: {duration}")
    kaggle_submission_df.to_csv("kaggle_submission_df.csv", index=False)
    logger.info(f"Shape of submission DF: {kaggle_submission_df.shape}")
    logger.info(kaggle_submission_df.head())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
    # 275s to load data with ray
    # 173.4898989200592s to load data without ray
