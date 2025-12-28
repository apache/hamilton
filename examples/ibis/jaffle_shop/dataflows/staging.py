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
import ibis.expr.types as ir


def customers(connection: ibis.BaseBackend, customers_source: str) -> ir.Table:
    """raw data about customers

    columns:
        - customer_id
        - first_name
        - last_name
    """
    return connection.read_parquet(customers_source, table_name="customers")[
        "id", "first_name", "last_name"
    ].rename(customer_id="id")


def orders(connection: ibis.BaseBackend, orders_source: str) -> ir.Table:
    """raw data about orders

    columns:
        - order_id
        - customer_id
        - order_date
        - status
    """
    return connection.read_parquet(orders_source, table_name="orders")[
        "id", "user_id", "order_date", "status"
    ].rename(order_id="id", customer_id="user_id")


def payments(connection: ibis.BaseBackend, payments_source: str) -> ir.Table:
    """raw data about payments; convert amount from cents to dollars

    columns:
        - payment_id
        - order_id
        - payment_method
        - amount
    """
    return (
        connection.read_parquet(payments_source, table_name="payments")[
            "id", "order_id", "payment_method", "amount"
        ]
        .rename(payment_id="id")
        .mutate(amount=ibis._.amount / 100)
    )
