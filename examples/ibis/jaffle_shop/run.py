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

import ibis

# import dataflow modules
from dataflows import customer_flow, order_flow, staging

from hamilton import driver


def main():
    # build Driver with dataflow modules
    dr = driver.Builder().with_modules(staging, customer_flow, order_flow).build()
    # create a visualization of the full dataflow
    dr.display_all_functions("all_functions.png")

    duckdb_connection = ibis.duckdb.connect("jaffleshop.duckdb")
    inputs = dict(
        connection=duckdb_connection,
        customers_source="data/raw_customers.parquet",
        orders_source="data/raw_orders.parquet",
        payments_source="data/raw_payments.parquet",
    )

    # results is a dictionary containing the Ibis expression, i.e., query plans
    outputs = dr.execute(["orders_final", "customers_final"], inputs=inputs)

    # execute the `orders_final` ibis expression to return a dataframe
    df = outputs["orders_final"].to_pandas()
    print(df.head())

    # execute the `customers_final` ibis expression to create a duckdb table
    duckdb_connection.execute(outputs["customers_final"])


if __name__ == "__main__":
    main()
