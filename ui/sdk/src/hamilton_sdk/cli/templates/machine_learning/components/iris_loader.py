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

from hamilton.function_modifiers import extract_columns

RAW_COLUMN_NAMES = [
    "sepal_length_cm",
    "sepal_width_cm",
    "petal_length_cm",
    "petal_width_cm",
]


def iris_data() -> utils.Bunch:
    return datasets.load_iris()


@extract_columns(*(RAW_COLUMN_NAMES + ["target_class"]))
def iris_df(iris_data: utils.Bunch) -> pd.DataFrame:
    _df = pd.DataFrame(iris_data.data, columns=RAW_COLUMN_NAMES)
    _df["target_class"] = [iris_data.target_names[t] for t in iris_data.target]
    return _df
