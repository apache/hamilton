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

The assumption here is that you need to go to a feature store to get RAW data, and in
the request you've only been passed
(alternatively if everything is in the feature store, you can skip the Hamilton step).

For the aggregation features, we load them from the feature store in this example.
"""

import fastapi
import features
import named_model_feature_sets
import online_loader
import pandas as pd
import pydantic

from hamilton import base
from hamilton.experimental import h_async

app = fastapi.FastAPI()

# creates a feature store client. This is just one way to do it.
feature_client = online_loader.FeatureStoreHttpClient("https://my-feature-store.com/")


@app.on_event("startup")
async def startup():
    """Starts a client for the life of the app. Required for the feature client."""
    feature_client.start()


# know the model schema somehow.
model_input_features = named_model_feature_sets.model_x_features


def fake_model_predict(df: pd.DataFrame) -> pd.Series:
    """Function to simulate a model.

    In real life this could deserialize a model from disk or a registry, and provide the function
    to use for prediction.
    """
    # do some transformation.
    return df.sum()  # this is nonsensical but provides a single number.


# you would load the model from disk or a registry -- here it's a function.
model_predict = fake_model_predict

# We instantiate an async driver once for the life of the app. We use the AsyncDriver here because under the hood
# FastAPI is async. If you were using Flask, you could use the regular Hamilton driver without issue.
dr = h_async.AsyncDriver(
    # pass in feature client because it's invariant to each execution.
    # pass in execution mode to construct things correctly.
    {"feature_client": feature_client, "execution_mode": "online"},
    online_loader,  # includes code to load data from the feature store.
    features,  # shared module of feature logic
    result_builder=base.SimplePythonDataFrameGraphAdapter(),
)


class PredictRequest(pydantic.BaseModel):
    """Here we assume we get just the client_id in the request."""

    client_id: str


@app.post("/predict")
async def predict_model_version1(request: PredictRequest) -> dict:
    """Illustrates how a prediction could be made that needs to go the feature store for features.

    In this version we go to the feature store, as part of the Hamilton DAG computation.
    But first,

    If you wanted  to visualize execution, you could do something like:
        dr.visualize_execution(model_input_features,
                                './online_execution.dot',
                                {"format": "png"},
                                inputs=input_series)

    :param request: the request body.
    :return: a dictionary with the prediction value.
    """
    # one liner to quickly create some series from the request.
    inputs = {"client_id": request.client_id}
    # create the features -- point here is we're reusing the same code as in the training!
    # with the ability to provide static values for things like `age_mean` and `age_std_dev`.
    features = await dr.execute(
        model_input_features,
        inputs=inputs,
    )
    dr.visualize_execution(
        model_input_features, "./online_execution.dot", {"format": "png"}, inputs=inputs
    )
    prediction = model_predict(features)
    return {"prediction": prediction.values[0]}


if __name__ == "__main__":
    # If you run this as a script, then the app will be started on localhost:8000
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

    # here's a request you can cut and past into http://localhost:8000/docs
    example_request_input = {
        "client_id": "some-id",  # remove this comma to make it valid JSON
    }
