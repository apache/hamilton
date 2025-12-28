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
from typing import List

import pandas as pd

"""This consists of data loading functions from from various sources.
For the sake of the demo, these are all mocked. First thing you'll want to do
is make them load from your sources (or, better, yet, use the load_from decorator!)
"""


def fabricate_client_login_data(client_ids: List[int]) -> pd.DataFrame:
    """Fabricates a dataframe of client login data.
    This contains the columns client ID (int) and last_logged_in (datetime)

    :param client_ids:
    :return:
    """

    ten_days = 60 * 60 * 24 * 10  # 10 days
    return pd.DataFrame(
        {
            "client_id": client_ids,
            "last_logged_in": [
                pd.Timestamp.now() - pd.Timedelta(seconds=random.randint(0, ten_days))
                for _ in client_ids
            ],
        }
    )


def fabricate_survey_results_data(client_ids: List[int]) -> pd.DataFrame:
    """Fabricates a dataframe of survey results.
    This has the following (random) columns:
    - budget -- amount they're willing to spend on an order (number between 1 and 1000)
    - age -- age of the client in years
    - gender -- either male or female
    - client_id -- the client ID

    :param client_ids: List of client IDs to fabricate data for
    :return: A dataframe of fabricated data
    """

    return pd.DataFrame(
        {
            "client_id": client_ids,
            "budget": [max(random.gauss(100, 50), 20) for _ in client_ids],
            "age": [random.randint(18, 100) for _ in client_ids],
            "gender": [["male", "female"][random.randint(0, 1)] for _ in client_ids],
        }
    )


def query_table(table: str, db: str, num_results: int = 100) -> pd.DataFrame:
    """This provides mock data loading capabilities for the purpose of this example.
    TODO -- replace with your own sources, using data loaders!

    :param table: Table to load from
    :param db: Database to load from
    :param num_results: Number of results to return
    :return: A preconfigured dataset
    """

    client_ids = list(range(1000))

    if table == "client_logins":
        return fabricate_client_login_data(client_ids)

    if table == "survey_results":
        return fabricate_survey_results_data(client_ids)


def query_survey_results(client_id: int) -> pd.DataFrame:
    """Queries survey results for a given client ID.

    :param client_id:
    :return:
    """
    return fabricate_survey_results_data([client_id])


def query_login_data(client_id: int) -> pd.DataFrame:
    """Queries login data for a given client ID."""
    return fabricate_client_login_data([client_id])


def query_scalar(value: str) -> float:
    """Mocks out querying a scalar value from a database."""

    if value == "age_mean":
        return 38.8
    if value == "age_stddev":
        return 13.5


if __name__ == "__main__":
    # use this to recreate the input CSV
    df = query_table("survey_results", "survey_results")
    print(df)
    df.to_csv("survey_results.csv", index=False)
