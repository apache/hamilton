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

import pandas as pd
from app import functions

from hamilton import driver

if __name__ == "__main__":
    df = pd.read_csv("/opt/ml/processing/input/data/input_table.csv")

    dr = driver.Driver({}, functions)

    inputs = {"input_table": df}

    output_columns = [
        "spend",
        "signups",
        "avg_3wk_spend",
        "spend_per_signup",
        "spend_zero_mean_unit_variance",
    ]

    # DAG visualization
    dot = dr.visualize_execution(final_vars=output_columns, inputs=inputs)
    with open("/opt/ml/processing/output/dag_visualization.svg", "wb") as svg_out:
        svg_out.write(dot.pipe(format="svg"))

    # DAG execution
    df_result = dr.execute(output_columns, inputs=inputs)
    df_result.to_csv("/opt/ml/processing/output/output_table.csv")
