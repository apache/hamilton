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

import pandas as pd
from components import utils

from hamilton.function_modifiers import config, extract_columns


@config.when(mode="batch")
@extract_columns("budget", "age", "gender", "client_id")
def survey_results(survey_results_table: str, survey_results_db: str) -> pd.DataFrame:
    """Map operation to explode survey results to all fields
    Data comes in JSON, we've grouped it into a series.
    """
    return utils.query_table(table=survey_results_table, db=survey_results_db)


@config.when(mode="online")
@extract_columns(
    "budget",
    "age",
    "gender",
)
def survey_results__online(client_id: int) -> pd.DataFrame:
    """Map operation to explode survey results to all fields
    Data comes in JSON, we've grouped it into a series.
    """
    return utils.query_survey_results(client_id=client_id)


@config.when(mode="streaming")
@extract_columns("budget", "age", "gender", "client_id")
def survey_results__streaming(survey_event: dict) -> pd.DataFrame:
    """Results come in from a survey event, which is just a dict passed to us by the upstream streaming engine."""
    return pd.DataFrame([survey_event])


@config.when(mode="batch")
def client_login_data__batch(client_login_db: str, client_login_table: str) -> pd.DataFrame:
    """Load the client login data"""
    return utils.query_table(table=client_login_table, db=client_login_db)


@config.when(mode="online")
def last_logged_in__online(client_id: int) -> pd.Series:
    """Query a service for the client login data"""
    return utils.query_login_data(client_id=client_id)["last_logged_in"]


@config.when(mode="streaming")
def last_logged_in__streaming(client_id: pd.Series) -> pd.Series:
    """Query a service for the client login data"""
    return utils.query_login_data(client_id=client_id)["last_logged_in"]
