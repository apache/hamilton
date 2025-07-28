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

import numpy as np
import pandas as pd
import pytest

from hamilton import node
from hamilton.data_quality.base import DataValidationError, ValidationResult
from hamilton.function_modifiers import (
    DATA_VALIDATOR_ORIGINAL_OUTPUT_TAG,
    IS_DATA_VALIDATOR_TAG,
    check_output,
    check_output_custom,
)
from hamilton.node import DependencyType

from tests.resources.dq_dummy_examples import (
    DUMMY_VALIDATORS_FOR_TESTING,
    SampleDataValidator2,
    SampleDataValidator3,
)


def test_check_output_node_transform():
    decorator = check_output(
        importance="warn",
        default_validator_candidates=DUMMY_VALIDATORS_FOR_TESTING,
        dataset_length=1,
        dtype=np.int64,
    )

    def fn(input: pd.Series) -> pd.Series:
        return input

    node_ = node.Node.from_fn(fn)
    subdag = decorator.transform_node(node_, config={}, fn=fn)
    assert 4 == len(subdag)
    subdag_as_dict = {node_.name: node_ for node_ in subdag}
    assert sorted(subdag_as_dict.keys()) == [
        "fn",
        "fn_dummy_data_validator_2",
        "fn_dummy_data_validator_3",
        "fn_raw",
    ]
    # TODO -- change when we change the naming scheme
    assert subdag_as_dict["fn_raw"].input_types["input"][1] == DependencyType.REQUIRED
    assert 3 == len(
        subdag_as_dict["fn"].input_types
    )  # Three dependencies -- the two with DQ + the original
    # The final function should take in everything but only use the raw results
    assert (
        subdag_as_dict["fn"].callable(
            fn_raw="test",
            fn_dummy_data_validator_2=ValidationResult(True, "", {}),
            fn_dummy_data_validator_3=ValidationResult(True, "", {}),
        )
        == "test"
    )


def test_check_output_custom_node_transform():
    decorator = check_output_custom(
        SampleDataValidator2(dataset_length=1, importance="warn"),
        SampleDataValidator3(dtype=np.int64, importance="warn"),
    )

    def fn(input: pd.Series) -> pd.Series:
        return input

    node_ = node.Node.from_fn(fn)
    subdag = decorator.transform_node(node_, config={}, fn=fn)
    assert 4 == len(subdag)
    subdag_as_dict = {node_.name: node_ for node_ in subdag}
    assert sorted(subdag_as_dict.keys()) == [
        "fn",
        "fn_dummy_data_validator_2",
        "fn_dummy_data_validator_3",
        "fn_raw",
    ]
    # TODO -- change when we change the naming scheme
    assert subdag_as_dict["fn_raw"].input_types["input"][1] == DependencyType.REQUIRED
    assert 3 == len(
        subdag_as_dict["fn"].input_types
    )  # Three dependencies -- the two with DQ + the original
    data_validators = [
        value
        for value in subdag_as_dict.values()
        if value.tags.get("hamilton.data_quality.contains_dq_results", False)
    ]
    assert len(data_validators) == 2  # One for each validator
    first_validator, _ = data_validators
    assert (
        IS_DATA_VALIDATOR_TAG in first_validator.tags
        and first_validator.tags[IS_DATA_VALIDATOR_TAG] is True
    )  # Validates that all the required tags are included
    assert (
        DATA_VALIDATOR_ORIGINAL_OUTPUT_TAG in first_validator.tags
        and first_validator.tags[DATA_VALIDATOR_ORIGINAL_OUTPUT_TAG] == "fn"
    )

    # The final function should take in everything but only use the raw results
    assert (
        subdag_as_dict["fn"].callable(
            fn_raw="test",
            fn_dummy_data_validator_2=ValidationResult(True, "", {}),
            fn_dummy_data_validator_3=ValidationResult(True, "", {}),
        )
        == "test"
    )


def test_check_output_custom_node_transform_duplicate():
    """You should be able to pass in the same validator twice; IRL it would be different args."""
    decorator = check_output_custom(
        SampleDataValidator2(dataset_length=1, importance="warn"),
        SampleDataValidator2(dataset_length=1, importance="warn"),
    )

    def fn(input: pd.Series) -> pd.Series:
        return input

    node_ = node.Node.from_fn(fn)
    subdag = decorator.transform_node(node_, config={}, fn=fn)
    assert 4 == len(subdag)
    subdag_as_dict = {node_.name: node_ for node_ in subdag}
    assert sorted(subdag_as_dict.keys()) == [
        "fn",
        "fn_dummy_data_validator_2",
        "fn_dummy_data_validator_2_1",
        "fn_raw",
    ]
    # TODO -- change when we change the naming scheme
    assert subdag_as_dict["fn_raw"].input_types["input"][1] == DependencyType.REQUIRED
    assert 3 == len(
        subdag_as_dict["fn"].input_types
    )  # Three dependencies -- the two with DQ + the original
    data_validators = [
        value
        for value in subdag_as_dict.values()
        if value.tags.get("hamilton.data_quality.contains_dq_results", False)
    ]
    assert len(data_validators) == 2  # One for each validator
    first_validator, _ = data_validators
    assert (
        IS_DATA_VALIDATOR_TAG in first_validator.tags
        and first_validator.tags[IS_DATA_VALIDATOR_TAG] is True
    )  # Validates that all the required tags are included
    assert (
        DATA_VALIDATOR_ORIGINAL_OUTPUT_TAG in first_validator.tags
        and first_validator.tags[DATA_VALIDATOR_ORIGINAL_OUTPUT_TAG] == "fn"
    )

    # The final function should take in everything but only use the raw results
    assert (
        subdag_as_dict["fn"].callable(
            fn_raw="test",
            fn_dummy_data_validator_2=ValidationResult(True, "", {}),
            fn_dummy_data_validator_2_1=ValidationResult(True, "", {}),
        )
        == "test"
    )


def test_check_output_custom_node_transform_raises_exception_with_failure():
    decorator = check_output_custom(
        SampleDataValidator2(dataset_length=1, importance="fail"),
        SampleDataValidator3(dtype=np.int64, importance="fail"),
    )

    def fn(input: pd.Series) -> pd.Series:
        return input

    node_ = node.Node.from_fn(fn)
    subdag = decorator.transform_node(node_, config={}, fn=fn)
    assert 4 == len(subdag)
    subdag_as_dict = {node_.name: node_ for node_ in subdag}

    with pytest.raises(DataValidationError):
        subdag_as_dict["fn"].callable(
            fn_raw=pd.Series([1.0, 2.0, 3.0]),
            fn_dummy_data_validator_2=ValidationResult(False, "", {}),
            fn_dummy_data_validator_3=ValidationResult(False, "", {}),
        )


def test_check_output_custom_node_transform_layered():
    decorator_1 = check_output_custom(
        SampleDataValidator2(dataset_length=1, importance="warn"),
    )

    decorator_2 = check_output_custom(SampleDataValidator3(dtype=np.int64, importance="warn"))

    def fn(input: pd.Series) -> pd.Series:
        return input

    node_ = node.Node.from_fn(fn)
    subdag_first_transformation = decorator_1.transform_dag([node_], config={}, fn=fn)
    subdag_second_transformation = decorator_2.transform_dag(
        subdag_first_transformation, config={}, fn=fn
    )
    # One node for each dummy validator
    # One final node
    # One intermediate node for each of the functions (E.G. raw)
    # TODO -- ensure that the intermediate nodes don't share names
    assert 5 == len(subdag_second_transformation)


def test_data_quality_constants_for_api_consistency():
    # simple tests to test data quality constants remain the same
    assert IS_DATA_VALIDATOR_TAG == "hamilton.data_quality.contains_dq_results"
    assert DATA_VALIDATOR_ORIGINAL_OUTPUT_TAG == "hamilton.data_quality.source_node"


def test_check_output_validation_error():
    """Tests that we wrap an error raised appropriately."""
    decorator = check_output(
        importance="warn",
        dtype=np.int64,
    )

    def fn(input: pd.Series) -> pd.DataFrame:
        return pd.DataFrame({"a": input})

    node_ = node.Node.from_fn(fn)
    with pytest.raises(ValueError) as e:
        decorator.transform_node(node_, config={}, fn=fn)
        assert "Could not resolve validators for @check_output for function [fn]" in str(e)
