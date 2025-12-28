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

import pandas as pd

from hamilton import base, driver

logging.basicConfig(stream=sys.stdout)

# we need to tell hamilton where to load function definitions from
# we use module pointers to do this
import my_functions

# This uses the module above, but you can pass in as many as you want
# In this case we want a dataframe output, but there are a host of other options
dr = driver.Builder().with_modules(my_functions).with_adapters(base.PandasDataFrameResult()).build()

# we need to specify what we want in the final results
# These can be string names or function pointers (E.G. my_functions.spend_per_signup)
output_columns = [
    "spend",
    "signups",
    "avg_3wk_spend",
    "spend_per_signup",
    "spend_zero_mean_unit_variance",
]

# We can also load these up from wherever we want, or even do so inside the
# DAG. For now we just hardcode them.
initial_columns = {
    "signups": pd.Series([1, 10, 50, 100, 200, 400]),
    "spend": pd.Series([10, 10, 20, 40, 40, 50]),
}
# let's compute the results!
df = dr.execute(output_columns, inputs=initial_columns)
print(df.to_string())

# To visualize do `pip install "sf-hamilton[visualization]"` if you want these to work
# Also look up visualize_path_between and visualize_execution
dr.display_all_functions("./my_dag.png")
