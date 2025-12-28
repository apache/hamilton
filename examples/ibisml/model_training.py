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

import ibis
import ibis.expr.types as ir
import ibisml
import pandas as pd
from sklearn.base import BaseEstimator, clone
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import KFold

from hamilton.function_modifiers import config, extract_fields
from hamilton.htypes import Collect, Parallelizable


@config.when(model="linear")
def base_model__linear() -> BaseEstimator:
    """Use Linear regression"""
    return LinearRegression()


@config.when(model="random_forest")
def base_model__random_forest() -> BaseEstimator:
    "Use Random forest regression"
    return RandomForestRegressor()


@config.when(model="boosting")
def base_model__boosting() -> BaseEstimator:
    "Use gradient boosting reression"
    return HistGradientBoostingRegressor()


def preprocessing_recipe() -> ibisml.Recipe:
    """Recipe to preprocess data for fitting and inference.
    We drop the temporary `idx` column generated to
    create cross validation splits
    """
    return ibisml.Recipe(
        ibisml.Drop(["idx"]),
        ibisml.ImputeMean(ibisml.numeric()),
        ibisml.ScaleStandard(ibisml.numeric()),
        ibisml.OneHotEncode(ibisml.nominal()),
    )


def data_split(
    feature_set: ir.Table,
    n_splits: int = 3,
) -> Parallelizable[tuple]:
    """Generate indices to create train/validation splits n times"""
    folds = KFold(n_splits=n_splits)
    idx = list(range(feature_set.count().execute()))
    feature_set = feature_set.mutate(idx=ibis.row_number())
    for train_idx, val_idx in folds.split(idx):
        train_set = feature_set.filter(ibis._.idx.isin(train_idx))
        val_set = feature_set.filter(ibis._.idx.isin(val_idx))
        yield train_set, val_set


@extract_fields(
    dict(
        X_train=pd.DataFrame,
        X_val=pd.DataFrame,
        y_train=pd.DataFrame,
        y_val=pd.DataFrame,
    )
)
def prepare_data(
    feature_set: ir.Table,
    label: str,
    data_split: tuple,
    preprocessing_recipe: ibisml.Recipe,
) -> dict:
    """Split data and apply preprocessing recipe"""
    train_set, val_set = data_split
    # add temporary idx column for train/val splits
    transform = preprocessing_recipe.fit(train_set, outcomes=[label])

    train = transform(train_set)
    df_train = train.to_pandas()
    X_train = df_train[train.features]
    y_train = df_train[train.outcomes].to_numpy().reshape(-1)

    df_test = transform(val_set).to_pandas()
    X_val = df_test[train.features]
    y_val = df_test[train.outcomes].to_numpy().reshape(-1)

    return dict(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
    )


def cross_validation_fold(
    X_train: pd.DataFrame,
    X_val: pd.DataFrame,
    y_train: pd.DataFrame,
    y_val: pd.DataFrame,
    base_model: BaseEstimator,
    data_split: tuple,
) -> dict:
    """Train model and make predictions on validation"""
    model = clone(base_model)

    model.fit(X_train, y_train)

    y_val_pred = model.predict(X_val)
    score = mean_squared_error(y_val, y_val_pred)

    return dict(y_true=y_val, y_pred=y_val_pred, score=score)


@extract_fields(
    dict(
        cross_validation_scores=list[float],
        cross_validation_preds=list[dict],
    )
)
def cross_validation_fold_collection(cross_validation_fold: Collect[dict]) -> dict:
    """Collect results from cross validation folds; separate predictions and
    performance scores into two variables"""
    scores, preds = [], []
    for fold in cross_validation_fold:
        scores.append(fold.pop("score"))
        preds.append(fold)
    return dict(
        cross_validation_scores=scores,
        cross_validation_preds=preds,
    )


def prediction_table(cross_validation_preds: list[dict]) -> ir.Table:
    """Create a table with cross validation predictions for future reference"""
    return ibis.memtable(cross_validation_preds)


def store_predictions(prediction_table: ir.Table) -> bool:
    """Store the cross validation predictions table somewhere
    Currently only returns True.
    """
    return True


@extract_fields(
    dict(
        full_model=BaseEstimator,
        fitted_recipe=ibisml.RecipeTransform,
    )
)
def train_full_model(
    feature_set: ir.Table,
    label: str,
    preprocessing_recipe: ibisml.Recipe,
    base_model: BaseEstimator,
) -> dict:
    """Train a model on the full dataset to use for inference."""
    transform = preprocessing_recipe.fit(feature_set, outcomes=[label])

    data = transform(feature_set)
    df = data.to_pandas()
    X = df[data.features]
    y = df[data.outcomes].to_numpy().reshape(-1)

    base_model.fit(X, y)
    return dict(
        full_model=base_model,
        fitted_recipe=transform,
    )
