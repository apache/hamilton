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

import sys

import pandas as pd

# awsglue is installed in the AWS Glue worker environment
from awsglue.utils import getResolvedOptions

from hamilton import driver
from hamilton_functions import functions

if __name__ == "__main__":
    args = getResolvedOptions(sys.argv, ["input-table", "output-table"])

    df = pd.read_csv(args["input_table"])

    dr = driver.Driver({}, functions)

    inputs = {"input_table": df}

    output_columns = [
        "spend",
        "signups",
        "avg_3wk_spend",
        "spend_per_signup",
        "spend_zero_mean_unit_variance",
    ]

    # DAG execution
    df_result = dr.execute(output_columns, inputs=inputs)
    df_result.to_csv(args["output_table"])
