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

# rename column
raw_dataset = raw_dataset.rename(columns={"Model Year": "ModelYear"})
print(raw_dataset.head().to_string())

# Do some feature engineering / data cleaning to create the data sets
# one hot encode -- we know the encoding here.
for value, country in {1: "USA", 2: "Europe", 3: "Japan"}.items():
    raw_dataset[country] = np.where(raw_dataset["Origin"] == value, 1, 0)
raw_dataset = raw_dataset.dropna()
# create data sets
train_test_split = 0.8
seed = 123
# split the pandas dataframe into train and test
train_dataset = raw_dataset.sample(frac=train_test_split, random_state=seed)
test_dataset = raw_dataset.drop(train_dataset.index)


# config for fitting a model
target_column: str = "MPG"

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

# evaluate the model - pull out target
test_labels = test_dataset.pop(target_column)

# convert boolean columns to integers for the model
bool_columns = test_dataset.select_dtypes(include=[bool]).columns
test_dataset[bool_columns] = test_dataset[bool_columns].astype(int)
test_dataset_scaled = scaler.transform(test_dataset)

# Predict and evaluate the model
test_pred = linear_model.predict(test_dataset_scaled)
mae = mean_absolute_error(test_labels, test_pred)
test_results = {"linear_model": mae}
print(test_results)
