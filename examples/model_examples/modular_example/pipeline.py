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

from typing import Any

import features
import inference
import pandas as pd
import train

from hamilton.function_modifiers import configuration, extract_fields, source, subdag


@extract_fields({"fit_model": Any, "training_prediction": pd.DataFrame})
@subdag(
    features,
    train,
    inference,
    inputs={
        "path": source("path"),
        "model_params": source("model_params"),
    },
    config={
        "model": configuration("train_model_type"),  # not strictly required but allows us to remap.
    },
)
def trained_pipeline(fit_model: Any, predicted_data: pd.DataFrame) -> dict:
    return {"fit_model": fit_model, "training_prediction": predicted_data}


@subdag(
    features,
    inference,
    inputs={
        "path": source("predict_path"),
        "fit_model": source("fit_model"),
    },
)
def predicted_data(predicted_data: pd.DataFrame) -> pd.DataFrame:
    return predicted_data
