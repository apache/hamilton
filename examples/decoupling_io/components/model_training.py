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

import pandas as pd
from sklearn import base, linear_model


def model_classifier(random_state: int) -> base.ClassifierMixin:
    """Creates an unfitted LR model object.

    :param random_state:
    :return:
    """
    lr = linear_model.LogisticRegression(random_state=random_state)
    return lr


def trained_model(
    model_classifier: base.ClassifierMixin, train_set: pd.DataFrame, target_column_name: str
) -> base.ClassifierMixin:
    """Fits a new model.

    :param model_classifier:
    :param train_set:
    :return:
    """
    feature_cols = [c for c in train_set.columns if c != target_column_name]
    model_classifier.fit(train_set[feature_cols], train_set[target_column_name])
    return model_classifier
