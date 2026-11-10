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

"""Functions with postponed annotations behind wrappers defined in another module.

Every annotation here is a string at runtime and names something only this module imports
(``Decimal``), so it resolves only against this module's namespace. Every function is a valid
node, so a Driver can be built from the module.
"""

from __future__ import annotations

from decimal import Decimal

from tests.resources import wrappers_from_another_module as wrappers


def price(amount: Decimal) -> Decimal:
    """Not decorated: the baseline."""
    return amount


@wrappers.passthrough
def price_with_tax(price: Decimal, tax_rate: Decimal) -> Decimal:
    """One ``functools.wraps`` layer."""
    return price * (1 + tax_rate)


@wrappers.passthrough
@wrappers.passthrough
def price_rounded(price_with_tax: Decimal) -> Decimal:
    """Two ``functools.wraps`` layers."""
    return price_with_tax.quantize(Decimal("0.01"))


@wrappers.fills_in(discount=Decimal("0.25"))
def price_discounted(price_rounded: Decimal, discount: Decimal) -> Decimal:
    """The wrapper hides ``discount`` from the signature."""
    return price_rounded * (1 - discount)


@wrappers.scaled_by_factor
def price_total(price_discounted: Decimal) -> Decimal:
    """The wrapper adds the ``factor`` parameter and its annotation."""
    return price_discounted


class Converter:
    """A callable object; Hamilton users pass its bound method where a function is expected."""

    def __init__(self, rate: Decimal):
        self.rate = rate

    def __call__(self, price: Decimal) -> Decimal:
        return price * self.rate
