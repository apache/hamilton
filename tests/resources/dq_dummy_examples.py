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

from typing import Type

import pandas as pd

from hamilton.data_quality.base import BaseDefaultValidator, DataValidator, ValidationResult


class SampleDataValidator1(BaseDefaultValidator):
    def __init__(self, equal_to: int, importance: str):
        super(SampleDataValidator1, self).__init__(importance=importance)
        self.equal_to = equal_to

    @classmethod
    def applies_to(cls, datatype: Type[Type]) -> bool:
        return datatype == int

    def description(self) -> str:
        return "Data must be equal to 10 to be valid"

    @classmethod
    def name(cls) -> str:
        return "dummy_data_validator_1"

    def validate(self, dataset: int) -> ValidationResult:
        passes = dataset == 10
        return ValidationResult(
            passes=passes,
            message=f"Data value: {dataset} {'does' if passes else 'does not'} equal {self.equal_to}",
        )

    @classmethod
    def arg(cls) -> str:
        return "equal_to"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.equal_to == other.equal_to


class SampleDataValidator2(DataValidator):
    def __init__(self, dataset_length: int, importance: str):
        super(SampleDataValidator2, self).__init__(importance=importance)
        self.dataset_length = dataset_length

    def description(self) -> str:
        return f"series must have length {self.dataset_length} to be valid"

    @classmethod
    def name(cls) -> str:
        return "dummy_data_validator_2"

    def validate(self, dataset: pd.Series) -> ValidationResult:
        passes = len(dataset) == self.dataset_length
        return ValidationResult(
            passes=passes,
            message=f"Dataset length is: {len(dataset)}. This {'passes' if passes else 'does not pass'}. It must be exactly '{self.dataset_length}",
            diagnostics={
                "dataset_length_must_be": self.dataset_length,
                "dataset_length_is": len(dataset),
            },
        )

    @classmethod
    def applies_to(cls, datatype: Type[Type]) -> bool:
        return datatype == pd.Series

    @classmethod
    def arg(cls) -> str:
        return "dataset_length"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.dataset_length == other.dataset_length


class SampleDataValidator3(DataValidator):
    def __init__(self, dtype: type, importance: str):
        super(SampleDataValidator3, self).__init__(importance=importance)
        self.dtype = dtype

    def description(self) -> str:
        return f"Series dtype must be {self.dtype} to be valid"

    @classmethod
    def name(cls) -> str:
        return "dummy_data_validator_3"

    def validate(self, dataset: pd.Series) -> ValidationResult:
        passes = dataset.dtype == self.dtype
        return ValidationResult(
            passes=passes,
            message=f"Dataset type is: {dataset.dtype}. This {'passes' if passes else 'does not pass'}. It must be '{self.dtype}",
            diagnostics={"required_dtype": str(self.dtype), "actual_dtype": str(dataset.dtype)},
        )

    @classmethod
    def applies_to(cls, datatype: Type[Type]) -> bool:
        return datatype == pd.Series

    @classmethod
    def arg(cls) -> str:
        return "dtype"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.dtype == other.dtype


DUMMY_VALIDATORS_FOR_TESTING = [SampleDataValidator1, SampleDataValidator2, SampleDataValidator3]
