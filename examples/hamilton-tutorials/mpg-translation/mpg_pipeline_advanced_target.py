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
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler

from hamilton.function_modifiers import extract_fields


def mpg_df() -> pd.DataFrame:
    url = "http://archive.ics.uci.edu/ml/machine-learning-databases/auto-mpg/auto-mpg.data"
    column_names = [
        "MPG",
        "Cylinders",
        "Displacement",
        "Horsepower",
        "Weight",
        "Acceleration",
        "Model Year",
        "Origin",
    ]

    raw_dataset = pd.read_csv(
        url, names=column_names, na_values="?", comment="\t", sep=" ", skipinitialspace=True
    )

    # some schema manipulation
    _mpg_df = raw_dataset.rename(columns={"Model Year": "ModelYear"})
    return _mpg_df


@extract_fields({"train_dataset": pd.DataFrame, "test_dataset": pd.DataFrame})
def data_sets(mpg_df: pd.DataFrame, train_test_split: float = 0.8, seed: int = 123) -> dict:
    # Do some feature engineering / data cleaning to create the data sets
    # one hot encode -- we know the encoding here.
    for value, country in {1: "USA", 2: "Europe", 3: "Japan"}.items():
        mpg_df[country] = np.where(mpg_df["Origin"] == value, 1, 0)
    raw_dataset = mpg_df.dropna()
    # split the pandas dataframe into train and test
    train_dataset = raw_dataset.sample(frac=train_test_split, random_state=seed)
    test_dataset = raw_dataset.drop(train_dataset.index)

    return {"train_dataset": train_dataset, "test_dataset": test_dataset}


def target_column() -> str:
    return "MPG"


@extract_fields({"lr_model": LinearRegression, "scaler": StandardScaler})
def linear_model(train_dataset: pd.DataFrame, target_column: str) -> dict:
    # Fit the model
    # pull out target
    train_labels = train_dataset.pop(target_column)
    # Convert boolean columns to integers for the model
    bool_columns = train_dataset.select_dtypes(include=[bool]).columns
    train_dataset[bool_columns] = train_dataset[bool_columns].astype(int)
    # Normalize the features for the model
    scaler = StandardScaler()
    train_dataset_scaled = scaler.fit_transform(train_dataset)

    # Initialize and fit the Linear Regression model
    linear_model = LinearRegression()
    linear_model.fit(train_dataset_scaled, train_labels)
    return {"lr_model": linear_model, "scaler": scaler}


def evaluated_model(
    lr_model: LinearRegression,
    scaler: StandardScaler,
    test_dataset: pd.DataFrame,
    target_column: str,
) -> dict:
    # evaluate the model - pull out target
    test_labels = test_dataset.pop(target_column)
    # Evaluate the model
    # convert boolean columns to integers for the model
    bool_columns = test_dataset.select_dtypes(include=[bool]).columns
    test_dataset[bool_columns] = test_dataset[bool_columns].astype(int)
    test_dataset_scaled = scaler.transform(test_dataset)

    # Predict and evaluate the model
    test_pred = lr_model.predict(test_dataset_scaled)
    mae = mean_absolute_error(test_labels, test_pred)
    test_results = {"linear_model": mae}
    return test_results


if __name__ == "__main__":
    import __main__
    from hamilton import driver

    dr = driver.Builder().with_modules(__main__).build()
    dr.display_all_functions("mpg_pipeline_advanced.png")
    result = dr.execute(["evaluated_model", "linear_model"])
    print(result)
