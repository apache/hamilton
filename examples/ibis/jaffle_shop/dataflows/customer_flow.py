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


def customer_orders(orders: ir.Table) -> ir.Table:
    """Aggregate statistics about previous customer orders"""
    return orders.group_by("customer_id").aggregate(
        first_order=orders.order_date.min(),
        most_recent_order=orders.order_date.max(),
        number_of_orders=orders.order_id.count(),
    )


def customer_payments(orders: ir.Table, payments: ir.Table) -> ir.Table:
    """Customer order and payment info"""
    return (
        payments.left_join(orders, "order_id")
        .group_by(orders.customer_id)
        .aggregate(total_amount=ibis._.amount.sum())
    )


def customers_final(
    customers: ir.Table, customer_orders: ir.Table, customer_payments: ir.Table
) -> ir.Table:
    """This table has basic information about a customer, as well as
    some derived facts based on a customer's orders

    customer_id: This is a unique identifier for a customer
    first_name: Customer's first name. PII.
    last_name: Customer's last name. PII.
    first_order: Date (UTC) of a customer's first order
    most_recent_order: Date (UTC) of a customer's most recent order
    number_of_orders: Count of the number of orders a customer has placed
    total_order_amount: Total value (AUD) of a customer's orders
    """
    return (
        customers.left_join(customer_orders, "customer_id")
        .drop("customer_id_right")
        .left_join(customer_payments, "customer_id")[
            "customer_id",
            "first_name",
            "last_name",
            "first_order",
            "most_recent_order",
            "number_of_orders",
            ibis._.total_amount.name("customer_lifetime_value"),
        ]
    )
