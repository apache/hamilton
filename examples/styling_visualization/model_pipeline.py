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

from typing import Dict, Union

import pandas as pd
from sklearn import base
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from hamilton.function_modifiers import extract_fields, tag


@extract_fields(
    {"X_train": pd.DataFrame, "X_test": pd.DataFrame, "y_train": pd.Series, "y_test": pd.Series}
)
def train_test_split_func(
    training_set_v1: pd.DataFrame,
    target: pd.Series,
    validation_size_fraction: float,
    random_state: int,
) -> Dict[str, Union[pd.DataFrame, pd.Series]]:
    """Function that creates the training & test splits.

    It this then extracted out into constituent components and used downstream.

    :param training_set_v1: feature matrix
    :param target: the target or the y
    :param validation_size_fraction:  the validation fraction
    :param random_state: random state for reproducibility
    :return: dictionary of dataframes and Series
    """

    X_train, X_test, y_train, y_test = train_test_split(
        training_set_v1,
        target,
        test_size=validation_size_fraction,
        stratify=target,
        random_state=random_state,
    )
    return {"X_train": X_train, "X_test": X_test, "y_train": y_train, "y_test": y_test}


def prefit_random_forest(random_state: int, max_depth: Union[int, None]) -> base.ClassifierMixin:
    """Returns a Random Forest Classifier with the specified parameters.

    :param random_state: random state for reproducibility.
    :param max_depth: the max depth of the forest.
    :return: an unfit Random Forest
    """
    return RandomForestClassifier(max_depth=max_depth, random_state=random_state)


@tag(owner="data-science", importance="production", artifact="model")
def fit_random_forest(
    prefit_random_forest: base.ClassifierMixin,
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> base.ClassifierMixin:
    """Calls fit on the classifier object; it mutates the classifier and fits it.

    :param prefit_random_forest: prefit classifier
    :param X_train: transformed features matrix
    :param y_train: target column
    :return: fit classifier - mutates the passed in object.
    """
    prefit_random_forest.fit(X_train, y_train)
    return prefit_random_forest
