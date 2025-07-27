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

from typing import Tuple

import data_loader
import ftrs_autoregression
import ftrs_calendar
import ftrs_common_prep
import pandas as pd


def create_training_features(data_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    config = {
        "data_path": data_path,
    }
    import os

    # dr = driver.Driver(config, data_loader, ftrs_autoregression, ftrs_calendar, ftrs_common_prep)
    from hamilton_sdk import driver

    dr = driver.Driver(
        config,
        data_loader,
        ftrs_autoregression,
        ftrs_calendar,
        ftrs_common_prep,
        project_id=31,
        api_key=os.environ["HAMILTON_API_KEY"],
        username="stefank@cs.stanford.edu",
        dag_name="ts-feature-engineering-v1",
        tags={"version": "v1", "stage": "production"},
    )
    all_possible_outputs = dr.list_available_variables()
    desired_features = [o.name for o in all_possible_outputs if o.tags.get("stage") == "production"]
    train_df = dr.execute(desired_features)
    return train_df.drop(["sales"], axis=1), train_df["sales"]


if __name__ == "__main__":
    # df = data_loader.sales_data_set("../data/train.csv")
    # sample = df[df["item"].isin([1, 2, 3])]
    # sample.to_csv("../data/train_sample.csv", index=False)
    # df.sample(frac=0.01).to_csv("../data/train_sample.csv", index=False)
    train, sales_col = create_training_features("../data/train_sample.csv")
    # print(train.head())
    # print(sales_col.head())
