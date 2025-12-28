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

import dataclasses
import os
from typing import List

import pandas as pd

from hamilton.function_modifiers import extract_columns, load_from, source
from hamilton.htypes import Collect, Parallelizable


def files(data_dir: str) -> List[str]:
    """Lists oll files in the data directory"""

    out = []
    for file in os.listdir(data_dir):
        if file.endswith(".csv"):
            out.append(os.path.join(data_dir, file))
    return out


@dataclasses.dataclass
class CityData:
    city: str
    weekend_file: str
    weekday_file: str


def city_data(files: List[str]) -> Parallelizable[CityData]:
    """Gathers a list of per-city data for processing/analyzing"""

    cities = dict()
    for file_name in files:
        city = os.path.basename(file_name).split("_")[0]
        is_weekend = file_name.endswith("weekends.csv")
        if city not in cities:
            cities[city] = CityData(city=city, weekend_file=None, weekday_file=None)
        if is_weekend:
            cities[city].weekend_file = file_name
        else:
            cities[city].weekday_file = file_name
    for city in cities.values():
        yield city


def weekend_file(city_data: CityData) -> str:
    """Returns the weekend file for a given city"""

    return city_data.weekend_file


def weekday_file(city_data: CityData) -> str:
    """Returns the weekday file for a given city"""

    return city_data.weekday_file


@load_from.csv(path=source("weekday_file"))
def weekday_data(wkd_data: pd.DataFrame) -> pd.DataFrame:
    return wkd_data


@load_from.csv(path=source("weekend_file"))
def weekend_data(wknd_data: pd.DataFrame) -> pd.DataFrame:
    return wknd_data


@extract_columns(
    "realSum", "room_type", "person_capacity", "guest_satisfaction_overall", "cleanliness_rating"
)
def all_data(weekday_data: pd.DataFrame, weekend_data: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([weekday_data, weekend_data])


def mean_guest_satisfaction(guest_satisfaction_overall: pd.Series) -> float:
    return guest_satisfaction_overall.mean()


def mean_price(realSum: pd.Series) -> float:
    return realSum.mean()


def mean_price_per_capacity(realSum: pd.Series, person_capacity: pd.Series) -> float:
    return (realSum / person_capacity).mean()


def mean_cleanliness(cleanliness_rating: pd.Series) -> float:
    return cleanliness_rating.mean()


def max_price(realSum: pd.Series) -> float:
    return realSum.max()


def statistics(
    mean_guest_satisfaction: float,
    mean_price: float,
    mean_price_per_capacity: float,
    mean_cleanliness: float,
    max_price: float,
    city_data: CityData,
) -> dict:
    """Basic aggregation to join the data together."""
    return {
        "mean_guest_satisfaction": mean_guest_satisfaction,
        "mean_price": mean_price,
        "mean_price_per_person": mean_price_per_capacity,
        "cleanliness_ratings_mean": mean_cleanliness,
        "max_price": max_price,
        "city": city_data.city,
    }


def statistics_by_city(statistics: Collect[dict]) -> pd.DataFrame:
    """Joins all data together"""
    return pd.DataFrame.from_records(statistics).set_index("city")
