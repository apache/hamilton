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

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from sklearn.base import BaseEstimator, clone
from sklearn.datasets import load_diabetes
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import KFold

from hamilton.function_modifiers import config, extract_fields


@extract_fields(dict(X_raw=np.ndarray, y=np.ndarray))
def load_data() -> dict:
    X_raw, y = load_diabetes(return_X_y=True)
    return dict(X_raw=X_raw, y=y)


def splits(X_raw: np.ndarray, n_splits: int = 3) -> list[tuple]:
    fold = KFold(n_splits=n_splits)
    return [(train_idx, eval_idx) for train_idx, eval_idx in fold.split(X_raw)]


@config.when_not_in(preprocess=["pca"])
def X__base(X_raw: np.ndarray) -> np.ndarray:
    return X_raw


@config.when(preprocess="pca")
def X__pca(X_raw: np.ndarray, n_components: int = 5) -> np.ndarray:
    pca = PCA(n_components=n_components)
    return pca.fit_transform(X_raw)


@config.when(model="linear")
def base_model__linear() -> BaseEstimator:
    return LinearRegression()


@config.when(model="random_forest")
def base_model__random_forest() -> BaseEstimator:
    return RandomForestRegressor()


@config.when(model="boosting")
def base_model__boosting() -> BaseEstimator:
    return HistGradientBoostingRegressor()


@extract_fields(
    dict(
        y_pred=np.ndarray,
        cv_scores=list,
    )
)
def cross_validation(
    X: np.ndarray,
    y: np.ndarray,
    base_model: BaseEstimator,
    splits: list[tuple],
) -> dict:
    cv_scores = []
    all_pred = np.zeros(y.shape[0])
    for train_idx, eval_idx in splits:
        model = clone(base_model)

        X_train, y_train = X[train_idx], y[train_idx]
        X_eval, y_eval = X[eval_idx], y[eval_idx]

        model.fit(X_train, y_train)

        y_eval_pred = model.predict(X_eval)
        all_pred[eval_idx] = y_eval_pred

        cv_score = mean_squared_error(y_eval, y_eval_pred)
        cv_scores.append(cv_score)

    return dict(y_pred=all_pred, cv_scores=cv_scores)


def trained_model(
    base_model: BaseEstimator,
    X: np.ndarray,
    y: np.ndarray,
) -> BaseEstimator:
    base_model.fit(X, y)
    return base_model


def prediction_df(y: np.ndarray, y_pred: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame.from_dict(dict(y_true=y, y_pred=y_pred), orient="columns")


def prediction_plot(y: np.ndarray, y_pred: np.ndarray) -> Figure:
    fig, ax = plt.subplots()
    ax.scatter(y, y_pred)
    ax.set_xlabel("True")
    ax.set_ylabel("Predicted")

    return fig
