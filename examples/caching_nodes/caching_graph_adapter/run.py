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

import logging
import pathlib
import sys

import business_logic
import data_loaders

from hamilton import base, driver
from hamilton.experimental import h_cache

logging.basicConfig(stream=sys.stdout)

# This is empty, we get the data from the data_loaders module
initial_columns = {}

cache_path = "tmp"
pathlib.Path(cache_path).mkdir(exist_ok=True)
adapter = h_cache.CachingGraphAdapter(cache_path, base.PandasDataFrameResult())
dr = driver.Driver(initial_columns, business_logic, data_loaders, adapter=adapter)
output_columns = [
    data_loaders.spend,
    data_loaders.signups,
    business_logic.avg_3wk_spend,
    business_logic.spend_per_signup,
    business_logic.spend_zero_mean_unit_variance,
]

df = dr.execute(output_columns)
print(df.to_string())
