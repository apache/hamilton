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
Module that contains logic to load data for the offline ETL process.

We use this to build our offline ETL featurization process.
"""

from typing import List

import aiohttp
import pandas as pd

from hamilton.function_modifiers import extract_columns
from hamilton.function_modifiers.expanders import extract_fields
from hamilton.function_modifiers.metadata import tag


class FeatureStoreHttpClient(object):
    """HTTP Client -- replace this with your own implementation if you need to."""

    session: aiohttp.ClientSession = None

    def __init__(self, url: str):
        self.url = url

    def start(self):
        self.session = aiohttp.ClientSession()

    async def stop(self):
        await self.session.close()
        self.session = None

    def __call__(self) -> aiohttp.ClientSession:
        assert self.session is not None
        return self.session

    async def get_features(self, client_id: str, features_needed: List[str]) -> pd.DataFrame:
        """Makes a request to the feature store to get the data.

        :param client_id: id of the client to get data for.
        :param features_needed: list of features to request from the feature store.
        :return: a dataframe with the requested features.
        """
        # Example request:
        # async with self.session.get(
        #     f"{self.url}/v0/features",
        #     params={
        #         "client_id": client_id,
        #         "features": features_needed,
        #     },
        # ) as resp:
        #     data = await resp.json()
        #     return pd.DataFrame(data["data"], index=[client_id])
        # But to make this example work without you setting up a feature store we'll just return some fake data.
        data = {
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
        return pd.DataFrame(data, index=[client_id])

    async def get_agg_features(self, entity_type: str) -> dict:
        """Gets the aggregate features for the entity type."""
        # Example request:
        # async with self.session.get(
        #     f"{self.url}/v0/agg_features",
        #     params={
        #         "entity_type": "client",
        #     },
        # ) as resp:
        #     data = await resp.json()
        #     return data
        # But to make this example work without you setting up a feature store we'll just return some fake data.
        return {"age_mean": 33.0, "age_std_dev": 13.0}


# full set of available columns from the data source
FEATURES_IN_STORE = [
    "reason_for_absence",
    "month_of_absence",
    "day_of_the_week",
    "seasons",
    "transportation_expense",
    "distance_from_residence_to_work",
    "service_time",
    "age",
    "work_load_average_per_day",
    "hit_target",
    "disciplinary_failure",
    "education",
    "son",
    "social_drinker",
    "social_smoker",
    "pet",
    "weight",
    "height",
    "body_mass_index",
]


@tag(source="feature_store")
@extract_columns(*FEATURES_IN_STORE)
async def raw_data(client_id: str, feature_client: FeatureStoreHttpClient) -> pd.DataFrame:
    """Extracts the raw data, renames the columns to be valid python variable names, and assigns an index.

    Note: we could get cleverer here and only request the features we need. We can use the Hamilton Driver to ask
    questions of the DAG for us to figure out what features we need, given some target outputs. For now, we just
    request all of them to keep this example simple. Hint: use `tags` here to know what are the "raw" features
    available in the feature store.

    :param client_id: id of the client to get data for.
    :param feature_client: the client to use to get features from.
    :return: a dataframe with features from the feature store.
    """
    data = await feature_client.get_features(client_id, FEATURES_IN_STORE)
    return data


@extract_fields({"age_mean": float, "age_std_dev": float})
async def aggregation_features(feature_client: FeatureStoreHttpClient) -> dict:
    """Grabs the aggregate features for "clients" as a whole.

    :param feature_client: the client to use to get features from.
    :return: the mean age of the employees.
    """
    data = await feature_client.get_agg_features("client")
    return data
