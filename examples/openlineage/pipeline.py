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

"""Revenue reporting with built-in SQL materializers.

- order_lines reads a query joining orders and customers from the sales database.
- daily_revenue aggregates in Python.
- revenue_report writes daily_revenue into the warehouse database.

No custom loader and no hand-written lineage metadata: the SQL materializers record the
datasource they used, and the OpenLineage adapter names the physical tables from it.
"""

import pandas as pd

from hamilton.function_modifiers import load_from, save_to, source, value

REVENUE_QUERY = """
-- paid order lines with the customer's country
WITH paid AS (SELECT * FROM orders WHERE status = 'paid')
SELECT p.order_date, c.country, p.amount
FROM paid p
JOIN customers c ON p.customer_id = c.id
"""


@load_from.sql(query_or_table=value(REVENUE_QUERY), db_connection=source("sales_db"))
def order_lines(df: pd.DataFrame) -> pd.DataFrame:
    return df


def daily_revenue(order_lines: pd.DataFrame) -> pd.DataFrame:
    return order_lines.groupby(["order_date", "country"], as_index=False)["amount"].sum()


@save_to.sql(
    table_name=value("daily_revenue"),
    db_connection=source("warehouse_db"),
    if_exists=value("replace"),
    index=value(False),
    output_name_="saved_revenue",
)
def revenue_report(daily_revenue: pd.DataFrame) -> pd.DataFrame:
    return daily_revenue
