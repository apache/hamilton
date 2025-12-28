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
from sklearn import preprocessing

from hamilton.function_modifiers.metadata import tag

# --- feature functions


def cabin_t(cabin: pd.Series) -> pd.Series:
    """Transforms raw cabin information to cabin type.

    :param cabin: cabin value
    :return: cabin type
    """
    return cabin.apply(lambda x: x[:1] if x is not np.nan else np.nan)


def ticket_t(ticket: pd.Series) -> pd.Series:
    """Transforms raw ticket information to ticket type.

    :param ticket: raw ticket number
    :return: ticket type
    """
    return ticket.apply(lambda x: str(x).split()[0])


def family(sibsp: pd.Series, parch: pd.Series) -> pd.Series:
    """Calculates the number of people in a family.

    :param sibsp: number of siblings
    :param parch: number of parents/children
    :return: number of people in family
    """
    return sibsp + parch


def _label_encoder(
    input_series: pd.Series,
) -> preprocessing.LabelEncoder:
    """Creates a label encoder and fits it to the input series.

    :param input_series: series to categorize
    :return: sklearn label encoder
    """
    le = preprocessing.LabelEncoder()
    le.fit(input_series)
    return le


def _label_transformer(
    fit_le: preprocessing.LabelEncoder,
    input_series: pd.Series,
) -> pd.Series:
    """Transforms the input series using the fit label encoder.

    :param fit_le: a fit label encoder
    :param input_series: series to transform
    :return: transformed series
    """
    return fit_le.transform(input_series)


def sex_encoder(sex: pd.Series) -> preprocessing.LabelEncoder:
    """Creates a label encoder for the sex feature and fits it to the input series."""
    return _label_encoder(sex)


def cabin_encoder(cabin: pd.Series) -> preprocessing.LabelEncoder:
    """Creates a label encoder for the cabin feature and fits it to the input series."""
    return _label_encoder(cabin)


def embarked_encoder(embarked: pd.Series) -> preprocessing.LabelEncoder:
    """Creates a label encoder for the embarked feature and fits it to the input series."""
    return _label_encoder(embarked)


def sex_category(sex: pd.Series, sex_encoder: preprocessing.LabelEncoder) -> pd.Series:
    """Creates sex category feature."""
    return _label_transformer(sex_encoder, sex)


def cabin_category(cabin: pd.Series, cabin_encoder: preprocessing.LabelEncoder) -> pd.Series:
    """Creates cabin category feature."""
    return _label_transformer(cabin_encoder, cabin)


def embarked_category(
    embarked: pd.Series, embarked_encoder: preprocessing.LabelEncoder
) -> pd.Series:
    """Creates embarked category feature."""
    return _label_transformer(embarked_encoder, embarked)


@tag(artifact="encoders", owner="data-science", importance="production")
def encoders(
    sex_encoder: preprocessing.LabelEncoder,
    cabin_encoder: preprocessing.LabelEncoder,
    embarked_encoder: preprocessing.LabelEncoder,
) -> dict:
    """Bundles up all the encoders so that they can be saved as a single artifact."""
    return {
        "sex_encoder": sex_encoder,
        "cabin_encoder": cabin_encoder,
        "embarked_encoder": embarked_encoder,
    }
