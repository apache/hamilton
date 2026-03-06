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

"""Test module with async functions decorated with data quality validators."""

from hamilton.data_quality.base import AsyncDataValidator, DataValidator, ValidationResult
from hamilton.function_modifiers import check_output_custom


class _AsyncPositiveValidator(AsyncDataValidator):
    def __init__(self):
        super().__init__(importance="fail")

    def applies_to(self, datatype: type[type]) -> bool:
        return datatype == int

    def description(self) -> str:
        return "Value must be positive"

    @classmethod
    def name(cls) -> str:
        return "async_positive_validator"

    async def validate(self, dataset: int) -> ValidationResult:
        passes = dataset > 0
        return ValidationResult(
            passes=passes,
            message=f"Value {dataset} is {'positive' if passes else 'not positive'}",
        )


class _SyncEvenValidator(DataValidator):
    def __init__(self):
        super().__init__(importance="warn")

    def applies_to(self, datatype: type[type]) -> bool:
        return datatype == int

    def description(self) -> str:
        return "Value should be even"

    @classmethod
    def name(cls) -> str:
        return "sync_even_validator"

    def validate(self, dataset: int) -> ValidationResult:
        passes = dataset % 2 == 0
        return ValidationResult(
            passes=passes,
            message=f"Value {dataset} is {'even' if passes else 'odd'}",
        )


def input_value() -> int:
    return 10


@check_output_custom(_AsyncPositiveValidator())
async def async_validated(input_value: int) -> int:
    return input_value * 2


@check_output_custom(_SyncEvenValidator())
async def sync_validated(input_value: int) -> int:
    return input_value + 2


@check_output_custom(_AsyncPositiveValidator(), _SyncEvenValidator())
async def mixed_validated(input_value: int) -> int:
    return input_value + 10
