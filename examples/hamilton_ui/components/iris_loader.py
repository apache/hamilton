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
Module to load iris data.
"""

import pandas as pd
from sklearn import datasets, utils

from hamilton.function_modifiers import config, extract_columns, load_from

RAW_COLUMN_NAMES = [
    "sepal_length_cm",
    "sepal_width_cm",
    "petal_length_cm",
    "petal_width_cm",
]


@config.when(case="api")
def iris_data_raw__api() -> utils.Bunch:
    return datasets.load_iris()


@extract_columns(*(RAW_COLUMN_NAMES + ["target_class"]))
@config.when(case="api")
def iris_df__api(iris_data_raw: utils.Bunch) -> pd.DataFrame:
    _df = pd.DataFrame(iris_data_raw.data, columns=RAW_COLUMN_NAMES)
    _df["target_class"] = [iris_data_raw.target_names[t] for t in iris_data_raw.target]
    return _df


@extract_columns(*(RAW_COLUMN_NAMES + ["target_class"]))
@load_from.parquet(path="iris.parquet")
@config.when(case="parquet")
def iris_df__parquet(iris_data_raw: pd.DataFrame) -> pd.DataFrame:
    return iris_data_raw
