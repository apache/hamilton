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


def total_amount_by_payment_method(payments: ir.Table) -> dict:
    """Create a column for each payment method indicating total amount spent"""
    return {
        f"{method}_amount": ibis.coalesce(
            payments.amount.sum(where=payments.payment_method == method), 0
        )
        for method in ["credit_card", "coupon", "bank_transfer", "gift_card"]
    }


def order_payments(
    payments: ir.Table,
    total_amount_by_payment_method: dict,
) -> ir.Table:
    """Aggregate total amount per order and decompose by payment method"""
    return payments.group_by("order_id").aggregate(
        **total_amount_by_payment_method, total_amount=payments.amount.sum()
    )


def orders_final(orders: ir.Table, order_payments: ir.Table) -> ir.Table:
    """This table has basic information about orders,
    as well as some derived facts based on payments

    order_id: This is a unique identifier for an order
    customer_id: Foreign key to the customers table
    order_date: Date (UTC) that the order was placed
    status: Orders can be one of the following statuses:
        - placed: The order has been placed but has not yet left the warehouse
        - shipped: The order has ben shipped to the customer and is currently in transit
        - completed: The order has been received by the customer
        - return_pending: The customer has indicated that they would like to return the order,
                          but it has not yet been received at the warehouse
        - returned: The order has been returned by the customer and received at the warehouse
    amount: Total amount (AUD) of the order
    credit_card_amount: Amount of the order (AUD) paid for by credit card
    coupon_amount: Amount of the order (AUD) paid for by coupon
    bank_transfer_amount: Amount of the order (AUD) paid for by bank transfer
    gift_card_amount: Amount of the order (AUD) paid for by gift card
    """
    return (
        orders.left_join(order_payments, "order_id")
        .select(
            "order_id", "customer_id", "order_date", "status", ibis.selectors.contains("amount")
        )
        .rename(amount="total_amount")
    )
