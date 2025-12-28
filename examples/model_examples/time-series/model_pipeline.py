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

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn import metrics
from sklearn.model_selection import TimeSeriesSplit

from hamilton.function_modifiers import does, extract_fields

logger = logging.getLogger(__name__)


def _create_dataframe(**kwargs) -> pd.DataFrame:
    """Internal helper function to create a dataframe from passed in str -> to pandas Series.

    :param kwargs: str -> pandas Series.
    :return: dataframe; assumption is that the indexes on the columns match.
    """
    return pd.DataFrame(kwargs)


@does(_create_dataframe)
def training_set(
    item_id_encoded: pd.Series,
    dept_id_encoded: pd.Series,
    cat_id_encoded: pd.Series,
    store_id_encoded: pd.Series,
    state_id_encoded: pd.Series,
    year: pd.Series,
    month: pd.Series,
    week: pd.Series,
    day: pd.Series,
    dayofweek: pd.Series,
    event_name_1_encoded: pd.Series,
    event_type_1_encoded: pd.Series,
    event_name_2_encoded: pd.Series,
    event_type_2_encoded: pd.Series,
    snap_CA: pd.Series,
    snap_TX: pd.Series,
    snap_WI: pd.Series,
    sell_price: pd.Series,
    lag_t28: pd.Series,
    lag_t29: pd.Series,
    lag_t30: pd.Series,
    rolling_mean_t7: pd.Series,
    rolling_std_t7: pd.Series,
    rolling_mean_t30: pd.Series,
    rolling_mean_t90: pd.Series,
    rolling_mean_t180: pd.Series,
    rolling_std_t30: pd.Series,
    price_change_t1: pd.Series,
    price_change_t365: pd.Series,
    rolling_price_std_t7: pd.Series,
    rolling_price_std_t30: pd.Series,
    date: pd.Series,
    demand: pd.Series,
) -> pd.DataFrame:
    """Function to capture the schema of our training set.

    We use @does just to show that we can use it; does delegates the body
    of this function to the one in the decorator, in this case _create_dataframe.
    """
    pass


@extract_fields({"x": pd.DataFrame, "y": pd.Series, "test": pd.DataFrame})
def data_sets(training_set: pd.DataFrame, cut_off_date: str = "2016-04-24") -> dict:
    """This functions creates the X, y, and test sets from the initial training set.

    :param training_set:
    :param cut_off_date:
    :return:
    """
    training_set.sort_values("date", inplace=True)
    x = training_set[(training_set["date"] <= cut_off_date)]
    y = x["demand"]
    test = training_set[(training_set["date"] > cut_off_date)]
    return {
        "x": x[list(set(x.columns) - {"demand", "date"})],
        "y": y,
        "test": test[list(set(x.columns) - {"demand"})],
    }


@extract_fields({"filled_test": pd.DataFrame, "feature_importances": pd.DataFrame})
def train_using_folds(
    x: pd.DataFrame,
    y: pd.Series,
    test: pd.DataFrame,
    n_fold: int,
    model_params: dict,
    num_boost_round: int = 2500,
    early_stopping_rounds: int = 50,
    log_evaluation: int = 100,
) -> dict:
    """Function that trains a model, and predicts demand and provides feature importances over time series folds.

    :param x: what we want to fit with.
    :param y: what we want to fit against.
    :param test: what we want to predict.
    :param n_fold: how many folds to use for time series splits.
    :param model_params: the dictionary of model parameters.
    :param num_boost_round: number of boosting rounds.
    :param early_stopping_rounds: number of early stopping rounds.
    :param log_evaluation: number of evaluations to do before logging.
    :return:
    """
    folds = TimeSeriesSplit(n_splits=n_fold)
    columns = [
        "item_id_encoded",
        "dept_id_encoded",
        "cat_id_encoded",
        "store_id_encoded",
        "state_id_encoded",
        "year",
        "month",
        "week",
        "day",
        "dayofweek",
        "event_name_1_encoded",
        "event_type_1_encoded",
        "event_name_2_encoded",
        "event_type_2_encoded",
        "snap_CA",
        "snap_TX",
        "snap_WI",
        "sell_price",
        "lag_t28",
        "lag_t29",
        "lag_t30",
        "rolling_mean_t7",
        "rolling_std_t7",
        "rolling_mean_t30",
        "rolling_mean_t90",
        "rolling_mean_t180",
        "rolling_std_t30",
        "price_change_t1",
        "price_change_t365",
        "rolling_price_std_t7",
        "rolling_price_std_t30",
    ]
    assert set(columns) == set(x.columns), "Error: columns aren't correct."
    splits = folds.split(x, y)
    y_preds = np.zeros(test.shape[0])
    y_oof = np.zeros(x.shape[0])
    feature_importances = pd.DataFrame()
    feature_importances["feature"] = columns
    mean_score = []
    for fold_n, (train_index, valid_index) in enumerate(splits):
        logger.info(f"Fold: {fold_n + 1}")
        X_train, X_valid = x.iloc[train_index], x.iloc[valid_index]
        y_train, y_valid = y.iloc[train_index], y.iloc[valid_index]
        clf = fit_lgb_model(
            X_train,
            X_valid,
            y_train,
            y_valid,
            early_stopping_rounds,
            log_evaluation,
            model_params,
            num_boost_round,
        )
        feature_importances[f"fold_{fold_n + 1}"] = clf.feature_importance()
        y_pred_valid = clf.predict(X_valid, num_iteration=clf.best_iteration)
        y_oof[valid_index] = y_pred_valid
        val_score = np.sqrt(metrics.mean_squared_error(y_pred_valid, y_valid))
        logger.info(f"val rmse score is {val_score}")
        mean_score.append(val_score)
        y_preds += predict_with_lgb_model(clf, test[list(set(test.columns) - {"date"})]) / n_fold
        del X_train, X_valid, y_train, y_valid
        gc.collect()
    logger.info(f"mean rmse score over folds is {np.mean(mean_score)}")
    test["demand"] = y_preds
    return {"filled_test": test, "feature_importances": feature_importances}


def predict_with_lgb_model(fit_lgb_model: lgb.Booster, X_test: pd.DataFrame) -> np.ndarray:
    """Predicts with a fitted lgb model.

    :param fit_lgb_model: the fitted lgb model.
    :param X_test: the test set.
    :return: column of predictions.
    """
    return fit_lgb_model.predict(X_test, num_iteration=fit_lgb_model.best_iteration)


def fit_lgb_model(
    X_train: pd.DataFrame,
    X_valid: pd.DataFrame,
    y_train: pd.Series,
    y_valid: pd.Series,
    early_stopping_rounds: int,
    log_evaluation: int,
    model_params: dict,
    num_boost_round: int,
) -> lgb.Booster:
    """Function to fit a lightgbm model.

    :param X_train:
    :param X_valid:
    :param y_train:
    :param y_valid:
    :param early_stopping_rounds:
    :param log_evaluation:
    :param model_params:
    :param num_boost_round:
    :return:
    """
    dtrain = lgb.Dataset(X_train, label=y_train)
    dvalid = lgb.Dataset(X_valid, label=y_valid)
    clf = lgb.train(
        model_params,
        dtrain,
        num_boost_round,
        valid_sets=[dtrain, dvalid],
        callbacks=[
            lgb.callback.early_stopping(early_stopping_rounds),
            lgb.callback.log_evaluation(log_evaluation),
        ],
    )
    return clf


def kaggle_submission_df(filled_test: pd.DataFrame, submission: pd.DataFrame) -> pd.DataFrame:
    """Given the filled in forecasted test set, massages it for submission.

    :param filled_test: the test set with the demand column filled in.
    :param submission: the submission dataframe.
    :return: massaged DF for submission.
    """
    predictions = filled_test[["date", "demand"]].copy()
    predictions["id"] = predictions.index
    predictions = pd.pivot(predictions, index="id", columns="date", values="demand").reset_index()
    predictions.columns = ["id"] + ["F" + str(i + 1) for i in range(28)]
    evaluation_rows = [row for row in submission["id"] if "evaluation" in row]
    evaluation = submission[submission["id"].isin(evaluation_rows)]
    validation = submission[["id"]].merge(predictions, on="id")
    final = pd.concat([validation, evaluation])
    return final
