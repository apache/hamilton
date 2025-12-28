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

from typing import Any

import pandas as pd

from hamilton.function_modifiers import config


@config.when(model="RandomForest")
def base_model__rf(model_params: dict) -> Any:
    from sklearn.ensemble import RandomForestClassifier

    return RandomForestClassifier(**model_params)


@config.when(model="LogisticRegression")
def base_model__lr(model_params: dict) -> Any:
    from sklearn.linear_model import LogisticRegression

    return LogisticRegression(**model_params)


@config.when(model="XGBoost")
def base_model__xgb(model_params: dict) -> Any:
    from xgboost import XGBClassifier

    return XGBClassifier(**model_params)


def fit_model(transformed_data: pd.DataFrame, base_model: Any) -> Any:
    """Fit a model to transformed data."""
    base_model.fit(transformed_data.drop("target", axis=1), transformed_data["target"])
    return base_model
