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


def orders_denormalized(orders: pd.DataFrame, order_details: pd.DataFrame) -> pd.DataFrame:
    _df = pd.merge(orders, order_details, how="inner", on=["order_id", "product_name"])
    _df["item_total"] = _df["unit_price"] * _df["quantity"]
    return _df


def orders_by_order_aggregates(orders_denormalized: pd.DataFrame) -> pd.DataFrame:
    _df = orders_denormalized.groupby(["order_id", "customer_name", "order_date"]).agg(
        {"item_total": "sum", "quantity": "sum"}
    )
    return _df
