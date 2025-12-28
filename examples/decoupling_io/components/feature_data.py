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
This is a module that contains our feature transforms.
"""

from typing import Dict, List, Set

import pandas as pd
from sklearn import impute, model_selection, preprocessing  # import KNNImputer

from hamilton.function_modifiers import extract_columns, extract_fields


def _sanitize_columns(
    df_columns: List[str],
) -> List[str]:
    """Helper function to sanitize column names.

    :param df_columns: the current column names
    :return: sanitized column names
    """
    return [c.strip().replace("/", "_per_").replace(" ", "_").lower() for c in df_columns]


@extract_columns("pclass", "sex", "age", "parch", "sibsp", "fare", "embarked", "name", "survived")
def passengers_df(titanic_data: pd.DataFrame) -> pd.DataFrame:
    """Function to take in a raw dataframe, check the output, and then extract columns.

    :param raw_passengers_df: the raw dataset we want to bring in.
    :return:
    """
    titanic_data = titanic_data.copy()
    titanic_data["pid"] = titanic_data.index
    raw_passengers_df = titanic_data.set_index("pid")  # create new DF.
    raw_passengers_df.columns = _sanitize_columns(raw_passengers_df.columns)
    return raw_passengers_df


def rare_titles() -> Set[str]:
    """Rare titles we've curated"""
    return {
        "Capt",
        "Col",
        "Don",
        "Dona",
        "Dr",
        "Jonkheer",
        "Lady",
        "Major",
        "Mlle",
        "Mme",
        "Ms",
        "Rev",
        "Sir",
        "the Countess",
    }


def family_size(parch: pd.Series, sibsp: pd.Series) -> pd.Series:
    return parch + sibsp


def normalized_name(name: pd.Series) -> pd.Series:
    """I believe this actually gets the honorific, not the name."""
    return name.apply(lambda x: x.split(",")[1].split(".")[0].strip())


def title(normalized_name: pd.Series, rare_titles: Set[str]) -> pd.Series:
    return normalized_name.apply(lambda n: "rare" if n in rare_titles else n)


def is_alone(family_size: pd.Series) -> pd.Series:
    return (family_size == 1).astype(int)


def one_hot_encoder() -> preprocessing.OneHotEncoder:
    return preprocessing.OneHotEncoder(handle_unknown="ignore", sparse=False)


def fit_categorical_encoder(
    one_hot_encoder: preprocessing.OneHotEncoder,
    embarked: pd.Series,
    sex: pd.Series,
    pclass: pd.Series,
    title: pd.Series,
    is_alone: pd.Series,
) -> preprocessing.OneHotEncoder:
    cat_df = pd.concat([embarked, sex, pclass, title, is_alone], axis=1)
    cat_df.columns = cat_df.columns.astype(str)
    one_hot_encoder.fit(cat_df)
    return one_hot_encoder


def categorical_df(
    fit_categorical_encoder: preprocessing.OneHotEncoder,
    embarked: pd.Series,
    sex: pd.Series,
    pclass: pd.Series,
    title: pd.Series,
    is_alone: pd.Series,
) -> pd.DataFrame:
    """This creates the dataframe of categorical features.

    The number of "features" output depends on the number of categories.

    :param fit_categorical_encoder:
    :param embarked:
    :param sex:
    :param pclass:
    :param title:
    :param is_alone:
    :return:
    """
    cat_df = pd.concat([embarked, sex, pclass, title, is_alone], axis=1)
    cat_df.columns = cat_df.columns.astype(str)
    cat_df = fit_categorical_encoder.transform(cat_df)
    df = pd.DataFrame(cat_df)
    df.index = embarked.index
    df.columns = [f"categorical_{c}" for c in df.columns]
    return df


def knn_imputer(n_neighbors: int = 5) -> impute.KNNImputer:
    return impute.KNNImputer(n_neighbors=n_neighbors)


def fit_knn_imputer(
    knn_imputer: impute.KNNImputer,
    age: pd.Series,
    fare: pd.Series,
    family_size: pd.Series,
) -> impute.KNNImputer:
    num_df = pd.concat([age, fare, family_size], axis=1)
    num_df.columns = num_df.columns.astype(str)
    knn_imputer.fit(num_df)
    return knn_imputer


def knn_imputed_df(
    fit_knn_imputer: impute.KNNImputer,
    age: pd.Series,
    fare: pd.Series,
    family_size: pd.Series,
) -> pd.DataFrame:
    """This creates the dataframe of KNN imputed numeric features.

    :param fit_knn_imputer:
    :param age:
    :param fare:
    :param family_size:
    :return:
    """
    num_df = pd.concat([age, fare, family_size], axis=1)
    num_df.columns = num_df.columns.astype(str)
    imputed_df = fit_knn_imputer.transform(num_df)
    df = pd.DataFrame(imputed_df)
    df.index = age.index
    df.columns = [f"knn_imputed_{c}" for c in df.columns]
    return df


def robust_scaler() -> preprocessing.RobustScaler:
    return preprocessing.RobustScaler()


def fit_scaler(
    robust_scaler: preprocessing.RobustScaler, knn_imputed_df: pd.DataFrame
) -> preprocessing.RobustScaler:
    robust_scaler.fit(knn_imputed_df)
    return robust_scaler


def scaled_numeric_df(
    fit_scaler: preprocessing.RobustScaler, knn_imputed_df: pd.DataFrame
) -> pd.DataFrame:
    """This creates the dataframe of scaled numeric features.

    :param fit_scaler:
    :param knn_imputed_df:
    :return:
    """
    num_df = fit_scaler.transform(knn_imputed_df)
    df = pd.DataFrame(num_df)
    df.index = knn_imputed_df.index
    df.columns = [f"scaled_numeric_{c}" for c in df.columns]
    return df


def data_set(
    scaled_numeric_df: pd.DataFrame, categorical_df: pd.DataFrame, target: pd.Series
) -> pd.DataFrame:
    """This function creates our dataset.

    Following what was in the code, this is how the features are stuck together.

    :param scaled_numeric_df:
    :param categorical_df:
    :param target:
    :return:
    """
    return pd.concat([scaled_numeric_df, categorical_df, target], axis=1)


def inference_set(scaled_numeric_df: pd.DataFrame, categorical_df: pd.DataFrame) -> pd.DataFrame:
    """This function creates an inference set.

    :param scaled_numeric_df:
    :param categorical_df:
    :return:
    """
    return pd.concat([scaled_numeric_df, categorical_df], axis=1)


def target(survived: pd.Series) -> pd.Series:
    """Just hard coding this mapping that we want survived to be our target.

    :param survived:
    :return:
    """
    target_col = survived.copy()
    target_col.name = "target"
    return target_col


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


def target_column_name() -> str:
    """Just hard coding this mapping that we want survived to be our target.

    :return:
    """
    return "target"
