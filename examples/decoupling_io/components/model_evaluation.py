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

import numpy as np
import pandas as pd
from sklearn import base, metrics


def y_train_estimation(
    trained_model: base.ClassifierMixin, train_set: pd.DataFrame, target_column_name: str
) -> np.ndarray:
    feature_cols = [c for c in train_set.columns if c != target_column_name]
    return trained_model.predict(train_set[feature_cols])


def y_train(train_set: pd.DataFrame, target_column_name: str) -> pd.Series:
    return train_set[target_column_name]


def cm_train(y_train: pd.Series, y_train_estimation: np.ndarray) -> np.ndarray:
    return metrics.confusion_matrix(y_train, y_train_estimation)


def y_test_estimation(
    trained_model: base.ClassifierMixin, test_set: pd.DataFrame, target_column_name: str
) -> np.ndarray:
    feature_cols = [c for c in test_set.columns if c != target_column_name]
    return trained_model.predict(test_set[feature_cols])


def y_test(test_set: pd.DataFrame, target_column_name: str) -> pd.Series:
    return test_set[target_column_name]


def cm_test(y_test: pd.Series, y_test_estimation: np.ndarray) -> np.ndarray:
    return metrics.confusion_matrix(y_test, y_test_estimation)


def model_predict(trained_model: base.ClassifierMixin, inference_set: pd.DataFrame) -> np.ndarray:
    return trained_model.predict(inference_set)


def confusion_matrix_test_plot(cm_test: np.ndarray) -> metrics.ConfusionMatrixDisplay:
    return metrics.ConfusionMatrixDisplay(cm_test)


def confusion_matrix_training_plot(cm_train: np.ndarray) -> metrics.ConfusionMatrixDisplay:
    return metrics.ConfusionMatrixDisplay(cm_train)
