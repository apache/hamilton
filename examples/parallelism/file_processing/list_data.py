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

from hamilton.htypes import Parallelizable


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
