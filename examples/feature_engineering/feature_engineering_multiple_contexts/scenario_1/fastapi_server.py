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

""" "
This is a simple example of a FastAPI server that uses Hamilton on the request
path to transform the data into features, and then uses a fake model to make
a prediction.

The assumption here is that you get all the raw data passed in via the request.

Otherwise for aggregation type features, you need to pass in a stored value
that we have mocked out with `load_invariant_feature_values`.

Note: we use the AsyncDriver here because under the hood FastAPI is async.
"""

import fastapi
import features
import named_model_feature_sets
import pandas as pd
import pydantic

from hamilton import async_driver, base

app = fastapi.FastAPI()

# know the model schema somehow.
model_input_features = named_model_feature_sets.model_x_features


def load_invariant_feature_values() -> dict:
    """This function would load the invariant feature values from a database or file.

    You would customize this to your needs.

    :return: a dictionary of invariant feature values.
    """
    return {
        "age_mean": 33.0,
        "age_std_dev": 12.0,
    }


def fake_model_predict(df: pd.DataFrame) -> pd.Series:
    """Function to simulate a model

    In real life this could deserialize a model from disk or a registry, and provide the function
    to use for prediction.
    """
    # do some transformation.
    return df.sum()  # this is nonsensical but provides a single number.


# you would load the model from disk or a registry -- here it's a function.
model_predict = fake_model_predict
# need to load the invariant features somehow.
invariant_feature_values = load_invariant_feature_values()

# We instantiate an async driver once for the life of the app. We use the AsyncDriver here because under the hood
# FastAPI is async. If you were using Flask, you could use the regular Hamilton driver without issue.
dr = async_driver.AsyncDriver(
    {},  # no config/invariant inputs in this example.
    features,  # the module that contains the common feature definitions.
    result_builder=base.SimplePythonDataFrameGraphAdapter(),
)


class PredictRequest(pydantic.BaseModel):
    """Assumption here is that all this data is available via the request that comes in."""

    id: int
    reason_for_absence: int
    month_of_absence: int
    day_of_the_week: int
    seasons: int
    transportation_expense: int
    distance_from_residence_to_work: int
    service_time: int
    age: int
    work_load_average_per_day: float
    hit_target: int
    disciplinary_failure: int
    education: int
    son: int
    social_drinker: int
    social_smoker: int
    pet: int
    weight: int
    height: int
    body_mass_index: int


@app.post("/predict")
async def predict_model_version1(request: PredictRequest) -> dict:
    """Illustrates how a prediction could be made that needs to compute some features first.
    In this version we go to the feature store, and then pass in what we get from the feature
    store as overrides to the model.

    If you wanted  to visualize execution, you could do something like:
        dr.visualize_execution(model_input_features,
                                './online_execution.dot',
                                {"format": "png"},
                                inputs=input_series)

    :param request: the request body.
    :return: a dictionary with the prediction value.
    """
    # one liner to quickly create some series from the request.
    input_series = pd.DataFrame([request.dict()]).to_dict(orient="series")
    # create the features -- point here is we're reusing the same code as in the training!
    # with the ability to provide static values for things like `age_mean` and `age_std_dev`.
    features = await dr.execute(
        model_input_features, inputs=input_series, overrides=invariant_feature_values
    )
    prediction = model_predict(features)
    return {"prediction": prediction.values[0]}


if __name__ == "__main__":
    # If you run this as a script, then the app will be started on localhost:8000
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

    # here's a request you can cut and past into http://localhost:8000/docs
    example_request_input = {
        "id": 11,
        "reason_for_absence": 26,
        "month_of_absence": 7,
        "day_of_the_week": 3,
        "seasons": 2,
        "transportation_expense": 1,
        "distance_from_residence_to_work": 1,
        "service_time": 289,
        "age": 36,
        "work_load_average_per_day": 13,
        "hit_target": 33,
        "disciplinary_failure": 239.554,
        "education": 97,
        "son": 0,
        "social_drinker": 1,
        "social_smoker": 2,
        "pet": 1,
        "weight": 90,
        "height": 172,
        "body_mass_index": 30,  # remove this comma to make it valid json.
    }
