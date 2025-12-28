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
This is a module that contains our "model fitting and related" transforms.
"""

import pickle
from typing import Dict

import numpy as np
import pandas as pd
from sklearn import base, linear_model, metrics, model_selection

from hamilton.function_modifiers import config, extract_fields


def target_column_name() -> str:
    """What column do we assume in the data set to be the target?"""
    return "target"


def model_classifier(random_state: int) -> base.ClassifierMixin:
    """Creates an unfitted LR model object.

    :param random_state:
    :return:
    """
    lr = linear_model.LogisticRegression(random_state=random_state)
    return lr


@extract_fields({"train_set": pd.DataFrame, "test_set": pd.DataFrame})
def train_test_split(
    data_set: pd.DataFrame, target: pd.Series, test_size: float
) -> Dict[str, pd.DataFrame]:
    """Splits the dataset into train & test.

    :param data_set: the dataset with all features already computed
    :param target: the target column. Used to stratify the training & test sets.
    :param test_size: the size of the test set to produce.
    :return:
    """
    train, test = model_selection.train_test_split(data_set, stratify=target, test_size=test_size)
    return {"train_set": train, "test_set": test}


@config.when(model_to_use="create_new")
def fit_model__create_new(
    model_classifier: base.ClassifierMixin,
    train_set: pd.DataFrame,
    target_column_name: str,
) -> base.ClassifierMixin:
    """Fits a new model.

    :param model_classifier:
    :param train_set:
    :return:
    """
    feature_cols = [c for c in train_set.columns if c != target_column_name]
    model_classifier.fit(train_set[feature_cols], train_set[target_column_name])
    return model_classifier


@config.when(model_to_use="use_existing")
def fit_model__use_existing(model_path: str) -> base.ClassifierMixin:
    with open(model_path, "rb") as f:
        return pickle.load(f)


def y_train_estimation(
    fit_model: base.ClassifierMixin, train_set: pd.DataFrame, target_column_name: str
) -> np.ndarray:
    feature_cols = [c for c in train_set.columns if c != target_column_name]
    return fit_model.predict(train_set[feature_cols])


def y_train(train_set: pd.DataFrame, target_column_name: str) -> pd.Series:
    return train_set[target_column_name]


def cm_train(y_train: pd.Series, y_train_estimation: np.ndarray) -> np.ndarray:
    return metrics.confusion_matrix(y_train, y_train_estimation)


def y_test_estimation(
    fit_model: base.ClassifierMixin, test_set: pd.DataFrame, target_column_name: str
) -> np.ndarray:
    feature_cols = [c for c in test_set.columns if c != target_column_name]
    return fit_model.predict(test_set[feature_cols])


def y_test(test_set: pd.DataFrame, target_column_name: str) -> pd.Series:
    return test_set[target_column_name]


def cm_test(y_test: pd.Series, y_test_estimation: np.ndarray) -> np.ndarray:
    return metrics.confusion_matrix(y_test, y_test_estimation)


def model_predict(fit_model: base.ClassifierMixin, inference_set: pd.DataFrame) -> np.ndarray:
    return fit_model.predict(inference_set)
