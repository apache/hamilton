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

import pyspark.pandas as ps
from pyspark.sql import SparkSession

from hamilton import base, driver, log_setup
from hamilton.plugins import h_spark

if __name__ == "__main__":
    log_setup.setup_logging(log_level=log_setup.LOG_LEVELS["INFO"])
    spark = SparkSession.builder.getOrCreate()
    # spark.sparkContext.setLogLevel('info')
    ps.set_option(
        "compute.ops_on_diff_frames", True
    )  # we should play around here on how to correctly initialize data.
    ps.set_option("compute.default_index_type", "distributed")  # this one doesn't seem to work?

    module_names = [
        "data_loaders",  # functions to help load data
        "business_logic",  # where our important logic lives
    ]
    modules = [importlib.import_module(m) for m in module_names]
    initial_config_and_or_data = {  # load from actuals or wherever
        "signups_location": "some_path",
        "spend_location": "some_other_path",
        "base_df_location": "some_other_other_path",
    }
    # df_container = ps.DataFrame(initial_config_and_or_data['spend'])  # assign spine column
    # Proving to myself that koalas works:
    # print(df_container)
    # import my_functions
    # df_container['spend_per_signup'] = my_functions.spend_per_signup(df_container['spend'], initial_columns['signups'])
    # df_container['avg_3wk_spend'] = my_functions.avg_3wk_spend(df_container['spend'])
    # df_container['spend_zero_mean_unit_variance'] = my_functions.spend_zero_mean_unit_variance(
    #     my_functions.spend_zero_mean(df_container['spend'], my_functions.spend_mean(df_container['spend'])),
    #     my_functions.spend_std_dev(df_container['spend'])
    # )
    # df_container['signups'] = initial_columns['signups']
    # print(df_container)
    """
   spend  spend_per_signup  avg_3wk_spend  spend_zero_mean_unit_variance  signups
0     10            10.000            NaN                      -1.064405        1
1     10             1.000            NaN                      -1.064405       10
2     20             0.400      13.333333                      -0.483821       50
3     40             0.400      23.333333                       0.677349      100
4     40             0.200      33.333333                       0.677349      200
5     50             0.125      43.333333                       1.257934      400
    """
    # okay hamilton is now doing its thing:
    skga = h_spark.SparkKoalasGraphAdapter(
        spark_session=spark,
        result_builder=base.PandasDataFrameResult(),
        # result_builder=h_spark.KoalasDataFrameResult(),
        spine_column="spend",
    )
    dr = driver.Driver(
        initial_config_and_or_data, *modules, adapter=skga
    )  # can pass in multiple modules
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
    # dr.visualize_execution(output_columns, "./pandas_on_spark", {"format": "png"})
    # dr.display_all_functions('./my_full_dag.dot')
    print(type(df))
    print(df.to_string())
    spark.stop()
    """
       spend  signups  avg_3wk_spend  spend_per_signup  spend_zero_mean_unit_variance
0     10        1            NaN            10.000                      -1.064405
1     10       10            NaN             1.000                      -1.064405
2     20       50      13.333333             0.400                      -0.483821
3     40      100      23.333333             0.400                       0.677349
4     40      200      33.333333             0.200                       0.677349
5     50      400      43.333333             0.125                       1.257934
    """
