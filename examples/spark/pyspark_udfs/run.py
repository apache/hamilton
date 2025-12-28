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

"""Spark driver and Hamilton driver code."""

import pandas as pd
from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

from hamilton import driver, log_setup
from hamilton.plugins import h_spark


def create_hamilton_driver(config: dict, modules: list) -> driver.Driver:
    """Helper function to create a Hamilton driver.

    :param config: any configuration required to instantiate a DAG.
    :param modules: the modules to crawl to get functions from to build the DAG.
    :return: an instantiated Hamilton driver.
    """
    adapter = h_spark.PySparkUDFGraphAdapter()
    dr = driver.Driver(config, *modules, adapter=adapter)  # can pass in multiple modules
    return dr


def get_hamilton_modules(use_pandas_udfs: bool) -> list:
    """We have two implementations of the same UDFs - this chooses which one to use.

    vanilla_udfs.py uses row based UDFs, pandas_udfs.py uses pandas UDFs which do compute
    that is vectorized.

    :param use_pandas_udfs: boolean, True to use pandas UDFs, False to use vanilla UDFs.
    :return: list of modules to pass to the Hamilton driver.
    """
    if use_pandas_udfs:
        import pandas_udfs

        modules = [pandas_udfs]
    else:
        import vanilla_udfs

        modules = [vanilla_udfs]
    return modules


def my_spark_job(spark: SparkSession, use_pandas_udfs: bool = False):
    """Template for a Spark job that uses Hamilton for their featuring engineering, i.e. any map, operations.

    :param spark: the SparkSession
    :param use_pandas_udfs: whether to use pandas UDFs or vanilla UDFs -- see code for details.
    """
    # replace this with SQL or however you'd get the data you need in.
    pandas_df = pd.DataFrame(
        {"spend": [10, 10, 20, 40, 40, 50], "signups": [1, 10, 50, 100, 200, 400]}
    )
    df = spark.createDataFrame(pandas_df)
    # add some extra values to the DF, e.g. aggregates, etc.
    df = add_values_to_dataframe(df)
    # get the modules that contain the UDFs
    modules = get_hamilton_modules(use_pandas_udfs)
    # create the Hamilton driver
    dr = create_hamilton_driver({}, modules)
    # create inputs to the UDFs - this needs to be column_name -> spark dataframe.
    execute_inputs = {col: df for col in df.columns}
    # add in any other scalar inputs/values/objects needed by the UDFs
    execute_inputs.update(
        {
            # "spend_mean": agg_values.first()["spend_mean"],
            # "spend_std_dev": agg_values.first()["spend_std_dev"],
            "foo": 1.0,
            "bar": 2.0,
        }
    )
    # tell Hamilton what columns need to be appended to the dataframe.
    cols_to_append = [
        "spend_per_signup",
        "spend_zero_mean_unit_variance",
        "foo",
        "bar",
        "augmented_mean",  # these can be function references too
    ]
    # visualize execution of what is going to be appended
    dr.visualize_execution(
        cols_to_append, "./my_spark_udf.dot", {"format": "png"}, inputs=execute_inputs
    )
    # tell Hamilton to tell Spark what to do
    df = dr.execute(cols_to_append, inputs=execute_inputs)
    # do other stuff -- you could filter, groupby, etc.
    w = Window.rowsBetween(-2, 0)
    df = df.withColumn("avg_3wk_spend", F.mean("spend").over(w))
    df = df.select(["spend", "signups", "avg_3wk_spend"] + cols_to_append)
    df.explain()
    df.show()
    # and you can reuse the same driver to execute UDFs on new dataframes:
    # df2 = spark.createDataFrame(pandas_df)
    # add some extra values to the DF, e.g. aggregates, etc.
    # df2 = add_values_to_dataframe(df2)
    # execute_inputs = {col: df2 for col in df2.columns}
    # df2 = dr.execute([
    #     "spend_per_signup",
    #     "spend_zero_mean_unit_variance",
    # ], inputs=execute_inputs)
    # df2.show()


def add_values_to_dataframe(df: DataFrame) -> DataFrame:
    """Helper function to add some extra columns to the dataframe.

    These are required to compute some of the UDFs. See comments for details.
    """
    # compute these values for some of the UDFs -- skip if you don't need them.
    agg_values = df.agg(F.mean("spend"), F.stddev("spend"))
    agg_values = agg_values.withColumnRenamed("avg(spend)", "spend_mean")
    agg_values = agg_values.withColumnRenamed("stddev_samp(spend)", "spend_std_dev")
    # we need a way to pass in the mean and std_dev to the UDFs - so add as columns.
    df = df.withColumn("spend_mean", F.lit(agg_values.first()["spend_mean"]))
    # df = df.withColumn("spend_mean", F.lit(10.0))  # or hard code the value
    df = df.withColumn("spend_std_dev", F.lit(agg_values.first()["spend_std_dev"]))
    # df = df.withColumn("spend_std_dev", F.lit(5.0))  # or hard code the value
    return df


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        use_pandas_udfs = sys.argv[1].lower() == "pandas"
    else:
        use_pandas_udfs = False
    log_setup.setup_logging(log_level=log_setup.LOG_LEVELS["INFO"])
    spark = SparkSession.builder.getOrCreate()
    spark.sparkContext.setLogLevel("info")

    my_spark_job(spark, use_pandas_udfs=use_pandas_udfs)
    # my_spark_job(spark, use_pandas_udfs=True)   # use pandas UDF functions
    # my_spark_job(spark, use_pandas_udfs=False)  # use vanilla UDF functions

    spark.stop()
