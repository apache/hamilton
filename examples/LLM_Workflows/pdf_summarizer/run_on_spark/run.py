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
import summarization
from pyspark.sql import SparkSession

from hamilton import driver, log_setup
from hamilton.plugins import h_spark


def my_spark_job(spark: SparkSession, openai_gpt_model: str, content_type: str, user_query: str):
    """Template for a Spark job that uses Hamilton for their featuring engineering, i.e. any map, operations.

    :param spark: the SparkSession
    :param openai_gpt_model: the model to use for summarization
    :param content_type: the content type of the document to summarize
    :param user_query: the user query to use for summarization
    """
    # replace this with SQL or however you'd get the data you need in.
    pandas_df = pd.DataFrame(
        # TODO: update this to point to a PDF or two.
        {"pdf_source": ["CDMS_HAMILTON_PAPER.pdf"]}
    )
    df = spark.createDataFrame(pandas_df)
    # get the modules that contain the UDFs
    modules = [summarization]
    driver_config = dict(file_type="pdf")
    # create the Hamilton driver
    adapter = h_spark.PySparkUDFGraphAdapter()

    dr = (
        driver.Builder()
        .with_config(driver_config)
        .with_modules(*modules)  # can pass in multiple modules
        .with_adapters(adapter)
        .build()
    )
    # create inputs to the UDFs - this needs to be column_name -> spark dataframe.
    execute_inputs = {col: df for col in df.columns}
    # add in any other scalar inputs/values/objects needed by the UDFs
    execute_inputs.update(
        dict(
            openai_gpt_model=openai_gpt_model,
            content_type=content_type,
            user_query=user_query,
        )
    )
    # tell Hamilton what columns need to be appended to the dataframe.
    cols_to_append = [
        "raw_text",
        "chunked_text",
        "summarized_text",
    ]
    # visualize execution of what is going to be appended
    dr.visualize_execution(
        cols_to_append,
        "./spark_summarization.dot",
        {"format": "png"},
        inputs=execute_inputs,
        deduplicate_inputs=True,
    )
    # tell Hamilton to tell Spark what to do
    df = dr.execute(cols_to_append, inputs=execute_inputs)
    df.explain()
    return df


if __name__ == "__main__":
    import os

    openai_api_key = os.environ.get("OPENAI_API_KEY")
    log_setup.setup_logging(log_level=log_setup.LOG_LEVELS["INFO"])
    # create the SparkSession -- note in real life, you'd adjust the number of executors to control parallelism.
    spark = SparkSession.builder.config(
        "spark.executorEnv.OPENAI_API_KEY", openai_api_key
    ).getOrCreate()
    spark.sparkContext.setLogLevel("info")
    # run the job
    _df = my_spark_job(spark, "gpt-3.5-turbo-0613", "Scientific article", "Can you ELI5 the paper?")
    # show the dataframe & thus make spark compute something
    _df.cache()
    _df.show()
    # you can also save the dataframe as a json file, parquet, etc.
    _df.write.json("processed_pdfs")
    spark.stop()
