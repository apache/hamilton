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

import importlib

import ray

from hamilton import base, driver, log_setup
from hamilton.plugins import h_ray

if __name__ == "__main__":
    log_setup.setup_logging()
    ray.init()
    module_names = [
        "data_loaders",  # functions to help load data
        "business_logic",  # where our important logic lives
    ]
    modules = [importlib.import_module(m) for m in module_names]
    initial_columns = {  # could load data here via some other means, or delegate to a module as we have done.
        # 'signups': pd.Series([1, 10, 50, 100, 200, 400]),
        "signups_location": "some_path",
        # 'spend': pd.Series([10, 10, 20, 40, 40, 50]),
        "spend_location": "some_other_path",
    }
    rga = h_ray.RayGraphAdapter(result_builder=base.PandasDataFrameResult())
    dr = driver.Driver(initial_columns, *modules, adapter=rga)  # can pass in multiple modules
    # we need to specify what we want in the final dataframe.
    output_columns = [
        "spend",
        "signups",
        "avg_3wk_spend",
        "spend_per_signup",
        "spend_zero_mean_unit_variance",
    ]
    # let's create the dataframe!
    df = dr.execute(output_columns)
    # To visualize do `pip install "sf-hamilton[visualization]"` if you want these to work
    # dr.visualize_execution(output_columns, "./ray_dag", {"format": "png"})
    # dr.display_all_functions('./my_full_dag.dot')
    print(df.to_string())
    ray.shutdown()
