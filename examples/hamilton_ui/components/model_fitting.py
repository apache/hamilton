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

"""This module contains basic code for model fitting."""

from typing import Dict

import numpy as np
import pandas as pd
from sklearn import base, linear_model, metrics, svm
from sklearn.model_selection import train_test_split

from hamilton import function_modifiers


@function_modifiers.config.when(clf="svm")
def prefit_clf__svm(gamma: float = 0.001) -> base.ClassifierMixin:
    """Returns an unfitted SVM classifier object.

    :param gamma: ...
    :return:
    """
    return svm.SVC(gamma=gamma)


@function_modifiers.config.when(clf="logistic")
def prefit_clf__logreg(penalty: str) -> base.ClassifierMixin:
    """Returns an unfitted Logistic Regression classifier object.

    :param penalty: One of {'l1', 'l2', 'elasticnet', None}.
    :return:
    """
    return linear_model.LogisticRegression(penalty)


@function_modifiers.extract_fields(
    {"X_train": pd.DataFrame, "X_test": pd.DataFrame, "y_train": pd.Series, "y_test": pd.Series}
)
def train_test_split_func(
    data_set: pd.DataFrame,
    test_size_fraction: float,
    shuffle_train_test_split: bool,
) -> Dict[str, np.ndarray]:
    """Function that creates the training & test splits.

    It this then extracted out into constituent components and used downstream.

    :param data_set:
    :param test_size_fraction:
    :param shuffle_train_test_split:
    :return:
    """
    assert "target_class" in data_set.columns, "target_class column must be present in the data set"
    feature_set = data_set[[col for col in data_set.columns if col != "target_class"]]
    target_class = data_set["target_class"]
    X_train, X_test, y_train, y_test = train_test_split(
        feature_set, target_class, test_size=test_size_fraction, shuffle=shuffle_train_test_split
    )
    return {"X_train": X_train, "X_test": X_test, "y_train": y_train, "y_test": y_test}


def fit_clf(
    prefit_clf: base.ClassifierMixin, X_train: pd.DataFrame, y_train: pd.Series
) -> base.ClassifierMixin:
    """Calls fit on the classifier object; it mutates it."""
    prefit_clf.fit(X_train, y_train)
    return prefit_clf


def training_accuracy(
    fit_clf: base.ClassifierMixin, X_train: pd.DataFrame, y_train: pd.Series
) -> float:
    """Returns accuracy on the training set."""
    return metrics.accuracy_score(fit_clf.predict(X_train), y_train)


def testing_accuracy(
    fit_clf: base.ClassifierMixin, X_test: pd.DataFrame, y_test: pd.Series
) -> float:
    """Returns accuracy on the test set."""
    return metrics.accuracy_score(fit_clf.predict(X_test), y_test)
