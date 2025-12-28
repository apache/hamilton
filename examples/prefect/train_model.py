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

from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, PoissonRegressor

from hamilton.function_modifiers import (
    config,
    extract_fields,
    load_from,
    parameterize,
    save_to,
    source,
)


@config.when(development_flag=False)
@load_from.csv(path=source("features_path"))
def preprocessed_data__prod(df: pd.DataFrame) -> pd.DataFrame:
    """Load stored preprocessed data"""
    return df


@config.when_not(development_flag=False)
@load_from.csv(path=source("features_path"))
def preprocessed_data__dev(df: pd.DataFrame) -> pd.DataFrame:
    """Load stored preprocessed data; only 20 rows"""
    return df.head(20)


@extract_fields(
    dict(
        train_df=pd.DataFrame,
        validation_df=pd.DataFrame,
    )
)
def split_indices(
    preprocessed_data: pd.DataFrame, validation_user_ids: List[int]
) -> Dict[str, pd.DataFrame]:
    """Creating train-validation splits based on the list of `validation_user_ids`"""
    validation_selection_mask = preprocessed_data.id.isin([int(i) for i in validation_user_ids])

    return dict(
        train_df=preprocessed_data.loc[~validation_selection_mask].copy(),
        validation_df=preprocessed_data.loc[validation_selection_mask].copy(),
    )


def data_stats(preprocessed_data: pd.DataFrame, feature_set: List[str]) -> pd.DataFrame:
    return preprocessed_data[feature_set].describe()


@parameterize(
    X_train=dict(df=source("train_df"), feature_set=source("feature_set")),
    X_validation=dict(df=source("validation_df"), feature_set=source("feature_set")),
)
def features(df: pd.DataFrame, feature_set: List[str]) -> np.ndarray:
    """Select features from `preprocessed_data` based on `feature_set`"""
    return df[feature_set].to_numpy()


@parameterize(
    y_train=dict(df=source("train_df")),
    y_validation=dict(df=source("validation_df")),
)
@config.when(task="binary_classification")
def target__binary_clf(df: pd.DataFrame) -> np.ndarray:
    """Binarize the labels based on a >=4h cutoff"""
    return np.where(df["absenteeism_time_in_hours"] >= 4, 1, 0)


@parameterize(
    y_train=dict(df=source("train_df")),
    y_validation=dict(df=source("validation_df")),
)
@config.when(task="continuous_regression")
def target__continuous_reg(df: pd.DataFrame) -> np.ndarray:
    """Do not transform labels; simply convert to numpy array"""
    return df["absenteeism_time_in_hours"].to_numpy()


@config.when(task="binary_classification")
def val_pred__binary_clf(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_validation: np.ndarray,
    y_validation: np.ndarray,
    model_config: dict,
) -> np.ndarray:
    """Train a binary logistic regression"""
    model = LogisticRegression(**model_config)
    model.fit(X_train, y_train)

    y_val_pred = model.predict(X_validation)
    return y_val_pred


@config.when(task="continuous_regression")
def val_pred__continuous_reg(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_validation: np.ndarray,
    y_validation: np.ndarray,
    model_config: dict,
) -> np.ndarray:
    """Train a poisson regression"""
    model = PoissonRegressor(**model_config)
    model.fit(X_train, y_train)

    y_val_pred = model.predict(X_validation)
    return y_val_pred


@save_to.csv(path=source("pred_path"), output_name_="save_val_pred")
def save_validation_preds(y_validation: np.ndarray, val_pred: np.ndarray) -> pd.DataFrame:
    """Save the model's predictions on the validation set"""
    return pd.DataFrame({"y_validation": y_validation, "val_pred": val_pred})
