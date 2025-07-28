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

import collections
import inspect
from typing import Any, Type

import numpy
import numpy as np
import pandas as pd
import pytest

import hamilton.data_quality.base
from hamilton.data_quality import default_validators
from hamilton.data_quality.base import BaseDefaultValidator
from hamilton.data_quality.default_validators import (
    AVAILABLE_DEFAULT_VALIDATORS,
    resolve_default_validators,
)

from tests.resources.dq_dummy_examples import (
    DUMMY_VALIDATORS_FOR_TESTING,
    SampleDataValidator1,
    SampleDataValidator2,
    SampleDataValidator3,
)


@pytest.mark.parametrize(
    "output_type, kwargs, importance, expected",
    [
        (int, {"equal_to": 1}, "warn", [SampleDataValidator1(importance="warn", equal_to=1)]),
        (int, {"equal_to": 5}, "fail", [SampleDataValidator1(importance="fail", equal_to=5)]),
        (
            pd.Series,
            {"dataset_length": 1},
            "warn",
            [SampleDataValidator2(importance="warn", dataset_length=1)],
        ),
        (
            pd.Series,
            {"dataset_length": 5},
            "fail",
            [SampleDataValidator2(importance="fail", dataset_length=5)],
        ),
        (
            pd.Series,
            {"dataset_length": 1, "dtype": np.int64},
            "warn",
            [
                SampleDataValidator2(importance="warn", dataset_length=1),
                SampleDataValidator3(importance="warn", dtype=np.int64),
            ],
        ),
    ],
)
def test_resolve_default_validators(output_type, kwargs, importance, expected):
    resolved_validators = resolve_default_validators(
        output_type=output_type,
        importance=importance,
        available_validators=DUMMY_VALIDATORS_FOR_TESTING,
        **kwargs,
    )
    assert resolved_validators == expected


@pytest.mark.parametrize(
    "output_type, kwargs, importance",
    [(str, {"dataset_length": 1}, "warn"), (pd.Series, {"equal_to": 1}, "warn")],
)
def test_resolve_default_validators_error(output_type, kwargs, importance):
    with pytest.raises(ValueError):
        resolve_default_validators(
            output_type=output_type,
            importance=importance,
            available_validators=DUMMY_VALIDATORS_FOR_TESTING,
            **kwargs,
        )


@pytest.mark.parametrize(
    "cls,param,data,should_pass",
    [
        (
            default_validators.DataInRangeValidatorPandasSeries,
            (0, 1),
            pd.Series([0.1, 0.2, 0.3]),
            True,
        ),
        (
            default_validators.DataInRangeValidatorPandasSeries,
            (0, 1),
            pd.Series([-30.0, 0.1, 0.2, 0.3, 100.0]),
            False,
        ),
        (default_validators.DataInValuesValidatorPandasSeries, [0, 1], pd.Series([0, 1, 1]), True),
        (
            default_validators.DataInValuesValidatorPandasSeries,
            [0.0, 1.0],
            pd.Series([0.0, 1.0, 1.0]),
            True,
        ),
        (
            default_validators.DataInValuesValidatorPandasSeries,
            ["a", "b"],
            pd.Series(["a", "b", "b"]),
            True,
        ),
        (default_validators.DataInValuesValidatorPandasSeries, [0], pd.Series([0, 1, 1]), False),
        (
            default_validators.DataInValuesValidatorPandasSeries,
            [0.0],
            pd.Series([0.0, 1.0, 1.0]),
            False,
        ),
        (
            default_validators.DataInValuesValidatorPandasSeries,
            ["a"],
            pd.Series(["a", "b", "b"]),
            False,
        ),
        (default_validators.DataInRangeValidatorPrimitives, (0, 1), 0.5, True),
        (default_validators.DataInRangeValidatorPrimitives, (0, 1), 100.3, False),
        (default_validators.DataInValuesValidatorPrimitives, [0, 1], 1, True),
        (default_validators.DataInValuesValidatorPrimitives, [0.0, 1.0], 1.0, True),
        (default_validators.DataInValuesValidatorPrimitives, ["a", "b"], "b", True),
        (default_validators.DataInValuesValidatorPrimitives, [0], 1, False),
        (default_validators.DataInValuesValidatorPrimitives, [0.0], 1.0, False),
        (default_validators.DataInValuesValidatorPrimitives, ["a"], "b", False),
        (
            default_validators.MaxFractionNansValidatorPandasSeries,
            0.5,
            pd.Series([1.0, 2.0, 3.0, None]),
            True,
        ),
        (
            default_validators.MaxFractionNansValidatorPandasSeries,
            0,
            pd.Series([1.0, 2.0, 3.0, None]),
            False,
        ),
        (
            default_validators.MaxFractionNansValidatorPandasSeries,
            0.5,
            pd.Series([1.0, 2.0, None, None]),
            True,
        ),
        (
            default_validators.MaxFractionNansValidatorPandasSeries,
            0.5,
            pd.Series([1.0, None, None, None]),
            False,
        ),
        (
            default_validators.MaxFractionNansValidatorPandasSeries,
            0.5,
            pd.Series([None, None, None, None]),
            False,
        ),
        (
            default_validators.MaxFractionNansValidatorPandasSeries,
            0,
            pd.Series([]),
            True,
        ),
        (
            default_validators.MaxFractionNansValidatorPandasSeries,
            1,
            pd.Series([]),
            True,
        ),
        (
            default_validators.DataTypeValidatorPandasSeries,
            numpy.dtype("int"),
            pd.Series([1, 2, 3]),
            True,
        ),
        (
            default_validators.DataTypeValidatorPandasSeries,
            numpy.dtype("int"),
            pd.Series([1.0, 2.0, 3.0]),
            False,
        ),
        (
            default_validators.DataTypeValidatorPandasSeries,
            numpy.dtype("object"),
            pd.Series(["hello", "goodbye"]),
            True,
        ),
        (
            default_validators.DataTypeValidatorPandasSeries,
            np.float64,
            pd.Series([2.3, 4.5, 6.6], dtype=pd.Float64Dtype()),
            True,
        ),
        (
            default_validators.DataTypeValidatorPandasSeries,
            numpy.dtype("object"),
            pd.Series([1, 2]),
            False,
        ),
        (default_validators.DataTypeValidatorPrimitives, int, 1, True),
        (default_validators.DataTypeValidatorPrimitives, str, "asdfasdf", True),
        (default_validators.DataTypeValidatorPrimitives, bool, True, True),
        (default_validators.DataTypeValidatorPrimitives, float, 2.0, True),
        (default_validators.DataTypeValidatorPrimitives, int, 1.0, False),
        (default_validators.DataTypeValidatorPrimitives, str, 1234, False),
        (default_validators.DataTypeValidatorPrimitives, bool, 0, False),
        (default_validators.DataTypeValidatorPrimitives, float, 2, False),
        (
            default_validators.MaxStandardDevValidatorPandasSeries,
            1.0,
            pd.Series([0.1, 0.2, 0.3, 0.4]),
            True,
        ),
        (
            default_validators.MaxStandardDevValidatorPandasSeries,
            0.01,
            pd.Series([0.1, 0.2, 0.3, 0.4]),
            False,
        ),
        (default_validators.AllowNaNsValidatorPandasSeries, False, pd.Series([0.1, None]), False),
        (default_validators.AllowNaNsValidatorPandasSeries, False, pd.Series([0.1, 0.2]), True),
        (default_validators.AllowNoneValidator, False, None, False),
        (default_validators.AllowNoneValidator, False, 1, True),
        (default_validators.AllowNoneValidator, True, None, True),
        (default_validators.AllowNoneValidator, True, 1, True),
        (default_validators.StrContainsValidator, "o b", "foo bar baz", True),
        (default_validators.StrContainsValidator, "oof", "foo bar baz", False),
        (default_validators.StrContainsValidator, ["o b", "baz"], "foo bar baz", True),
        (default_validators.StrContainsValidator, ["oof", "bar"], "foo bar baz", False),
        (default_validators.StrDoesNotContainValidator, "o b", "foo bar baz", False),
        (default_validators.StrDoesNotContainValidator, "oof", "foo bar baz", True),
        (default_validators.StrDoesNotContainValidator, ["o b", "boo"], "foo bar baz", False),
        (default_validators.StrDoesNotContainValidator, ["oof", "boo"], "foo bar baz", True),
    ],
)
def test_default_data_validators(
    cls: Type[hamilton.data_quality.base.BaseDefaultValidator],
    param: Any,
    data: Any,
    should_pass: bool,
):
    validator = cls(**{cls.arg(): param, "importance": "warn"})
    result = validator.validate(data)
    assert result.passes == should_pass


def test_to_ensure_all_validators_added_to_default_validator_list():
    def predicate(maybe_cls: Any) -> bool:
        if not inspect.isclass(maybe_cls):
            return False
        return issubclass(maybe_cls, BaseDefaultValidator) and maybe_cls != BaseDefaultValidator

    all_subclasses = inspect.getmembers(default_validators, predicate)
    missing_classes = [
        item
        for (_, item) in all_subclasses
        if item not in default_validators.AVAILABLE_DEFAULT_VALIDATORS
    ]
    assert len(missing_classes) == 0


def test_that_all_validators_with_the_same_arg_have_the_same_name():
    kwarg_to_name_map = {}
    conflicting = collections.defaultdict(list)
    for validator in AVAILABLE_DEFAULT_VALIDATORS:
        print(validator.arg(), validator.name())
        if validator.arg() not in kwarg_to_name_map:
            kwarg_to_name_map[validator.arg()] = validator.name()
        if kwarg_to_name_map[validator.arg()] != validator.name():
            conflicting[validator.arg()] = validator.name()
    if len(conflicting) > 0:
        raise ValueError(
            f"The following args have multiple classes with different corresponding names. "
            f"Validators with the same arg must all have the same name: {conflicting}"
        )
