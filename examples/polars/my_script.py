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
import sys

from hamilton import base, driver
from hamilton.plugins import h_polars

logging.basicConfig(stream=sys.stdout)

# Create a driver instance.
adapter = base.SimplePythonGraphAdapter(result_builder=h_polars.PolarsDataFrameResult())
config = {
    "base_df_location": "dummy_value",
}
import my_functions  # where our functions are defined

dr = driver.Driver(config, my_functions, adapter=adapter)
# note -- currently the result builder does not handle mixed outputs, e.g. Series and scalars.
output_columns = [
    "spend",
    "signups",
    "avg_3wk_spend",
    "spend_per_signup",
    "spend_zero_mean_unit_variance",
]
# let's create the dataframe!
df = dr.execute(output_columns)
print(df)

# To visualize do `pip install "sf-hamilton[visualization]"` if you want these to work
# dr.visualize_execution(output_columns, './polars', {"format": "png"})
# dr.display_all_functions('./my_full_dag.dot')
