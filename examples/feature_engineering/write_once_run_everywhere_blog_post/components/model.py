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

import random

import pandas as pd
from pandas import DataFrame


# This is a simple placeholder for a model. You'll likely want to adjust the typing to make it
# work for your case, or use a pretrained model.
class Model:
    def predict(self, features: DataFrame) -> pd.Series:
        return pd.Series([random.random() for item in features.iterrows()])


def model() -> Model:
    return Model()


def features(
    time_since_last_login: pd.Series,
    is_male: pd.Series,
    is_female: pd.Series,
    is_high_roller: pd.Series,
    age_normalized: pd.Series,
) -> pd.DataFrame:
    """Aggregate all features into a single dataframe.
    :param time_since_last_login: Feature the model cares about
    :param is_male: Feature the model cares about
    :param is_female: Feature the model cares about
    :param is_high_roller: Feature the model cares about
    :param age_normalized: Feature the model cares about
    :return: All features concatenated into a single dataframe
    """
    return pd.DataFrame(locals())


def predictions(features: pd.DataFrame, model: Model) -> pd.Series:
    """Simple call to your model over your features."""
    return model.predict(features)
