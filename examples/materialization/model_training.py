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

from typing import Dict

import numpy as np
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

    :param penalty:
    :return:
    """
    return linear_model.LogisticRegression(penalty)


@function_modifiers.extract_fields(
    {"X_train": np.ndarray, "X_test": np.ndarray, "y_train": np.ndarray, "y_test": np.ndarray}
)
def train_test_split_func(
    feature_matrix: np.ndarray,
    target: np.ndarray,
    test_size_fraction: float,
    shuffle_train_test_split: bool,
) -> Dict[str, np.ndarray]:
    """Function that creates the training & test splits.

    It this then extracted out into constituent components and used downstream.

    :param feature_matrix:
    :param target:
    :param test_size_fraction:
    :param shuffle_train_test_split:
    :return:
    """
    X_train, X_test, y_train, y_test = train_test_split(
        feature_matrix, target, test_size=test_size_fraction, shuffle=shuffle_train_test_split
    )
    return {"X_train": X_train, "X_test": X_test, "y_train": y_train, "y_test": y_test}


def y_test_with_labels(y_test: np.ndarray, target_names: np.ndarray) -> np.ndarray:
    """Adds labels to the target output."""
    return np.array([target_names[idx] for idx in y_test])


def fit_clf(
    prefit_clf: base.ClassifierMixin, X_train: np.ndarray, y_train: np.ndarray
) -> base.ClassifierMixin:
    """Calls fit on the classifier object; it mutates it."""
    prefit_clf.fit(X_train, y_train)
    return prefit_clf


def predicted_output(fit_clf: base.ClassifierMixin, X_test: np.ndarray) -> np.ndarray:
    """Exercised the fit classifier to perform a prediction."""
    return fit_clf.predict(X_test)


def predicted_output_with_labels(
    predicted_output: np.ndarray, target_names: np.ndarray
) -> np.ndarray:
    """Replaces the predictions with the desired labels."""
    return np.array([target_names[idx] for idx in predicted_output])


def classification_report(
    predicted_output_with_labels: np.ndarray, y_test_with_labels: np.ndarray
) -> str:
    """Returns a classification report."""
    return metrics.classification_report(y_test_with_labels, predicted_output_with_labels)


def confusion_matrix(
    predicted_output_with_labels: np.ndarray, y_test_with_labels: np.ndarray
) -> str:
    """Returns a confusion matrix report."""
    return metrics.confusion_matrix(y_test_with_labels, predicted_output_with_labels)


def model_parameters(fit_clf: base.ClassifierMixin) -> dict:
    """Returns a dictionary of model parameters."""
    return fit_clf.get_params()
