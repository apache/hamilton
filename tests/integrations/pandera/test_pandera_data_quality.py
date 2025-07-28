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

import sys

import dask.dataframe as dd
import numpy as np
import pandas as pd
import pandera as pa
import pytest

from hamilton import node
from hamilton.data_quality import pandera_validators
from hamilton.function_modifiers import base
from hamilton.plugins import h_pandera


def test_basic_pandera_decorator_dataframe_fails():
    schema = pa.DataFrameSchema(
        {
            "column1": pa.Column(int),
            "column2": pa.Column(float, pa.Check(lambda s: s < -1.2)),
            # you can provide a list of validators
            "column3": pa.Column(
                str,
                [
                    pa.Check(lambda s: s.str.startswith("value")),
                    pa.Check(lambda s: s.str.split("_", expand=True).shape[1] == 2),
                ],
            ),
        },
        index=pa.Index(int),
        strict=True,
    )

    df = pd.DataFrame({"column1": [5, 1, np.nan]})
    validator = pandera_validators.PanderaDataFrameValidator(schema=schema, importance="warn")
    validation_result = validator.validate(df)
    assert not validation_result.passes
    assert len(validation_result.diagnostics["schema_errors"]) == 4


def test_basic_pandera_decorator_dataframe_passes():
    schema = pa.DataFrameSchema(
        {
            "column1": pa.Column(int),
            "column2": pa.Column(float, pa.Check(lambda s: s < -1.2)),
            # you can provide a list of validators
            "column3": pa.Column(
                str,
                [
                    pa.Check(lambda s: s.str.startswith("value")),
                    pa.Check(lambda s: s.str.split("_", expand=True).shape[1] == 2),
                ],
            ),
        },
        index=pa.Index(int),
        strict=True,
    )

    df = pd.DataFrame(
        {
            "column1": [5, 1, 0],
            "column2": [-2.0, -1.9, -20.0],
            "column3": ["value_0", "value_1", "value_2"],
        }
    )
    validator = pandera_validators.PanderaDataFrameValidator(schema=schema, importance="warn")
    validation_result = validator.validate(df)
    assert validation_result.passes


def test_basic_pandera_decorator_series_fails():
    schema = pa.SeriesSchema(
        str,
        checks=[
            pa.Check(lambda s: s.str.startswith("foo")),
            pa.Check(lambda s: s.str.endswith("bar")),
            pa.Check(lambda x: len(x) > 3, element_wise=True),
        ],
        nullable=False,
    )
    series = pd.Series(["foobar", "foobox", "foobaz"])
    validator = pandera_validators.PanderaSeriesSchemaValidator(schema=schema, importance="warn")
    validation_result = validator.validate(series)
    assert not validation_result.passes
    assert len(validation_result.diagnostics["schema_errors"]) == 1


def test_basic_pandera_decorator_series_passes():
    schema = pa.SeriesSchema(
        str,
        checks=[
            pa.Check(lambda s: s.str.startswith("foo")),
            pa.Check(lambda s: s.str.endswith("bar")),
            pa.Check(lambda x: len(x) > 3, element_wise=True),
        ],
        nullable=False,
    )
    series = pd.Series(["foobar", "foo_bar", "foo__bar"])
    validator = pandera_validators.PanderaSeriesSchemaValidator(schema=schema, importance="warn")
    validation_result = validator.validate(series)
    assert validation_result.passes


def test_pandera_decorator_creates_correct_validator():
    class OutputSchema(pa.DataFrameModel):
        year: pa.typing.pandas.Series[int] = pa.Field(gt=2000, coerce=True)
        month: pa.typing.pandas.Series[int] = pa.Field(ge=1, le=12, coerce=True)
        day: pa.typing.pandas.Series[int] = pa.Field(ge=0, le=365, coerce=True)

    def foo(should_break: bool = False) -> pa.typing.pandas.DataFrame[OutputSchema]:
        if should_break:
            return pd.DataFrame(
                {
                    "year": ["-2001", "-2002", "-2003"],
                    "month": ["-13", "-6", "120"],
                    "day": ["700", "-156", "367"],
                }
            )
        return pd.DataFrame(
            {
                "year": ["2001", "2002", "2003"],
                "month": ["3", "6", "12"],
                "day": ["200", "156", "365"],
            }
        )

    n = node.Node.from_fn(foo)
    validators = h_pandera.check_output().get_validators(n)
    assert len(validators) == 1
    (validator,) = validators
    result_success = validator.validate(n())  # should not fail
    assert result_success.passes
    result_failed = validator.validate(n(should_break=True))  # should fail
    assert not result_failed.passes


def test_pandera_decorator_fails_without_annotation():
    def foo() -> pd.DataFrame:
        return pd.DataFrame(
            {
                "year": ["2001", "2002", "2003"],
                "month": ["3", "6", "12"],
                "day": ["200", "156", "365"],
            }
        )

    n = node.Node.from_fn(foo)
    with pytest.raises(base.InvalidDecoratorException):
        h_pandera.check_output().get_validators(n)


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_pandera_decorator_dask_df():
    """Validates that the function can be annotated with a dask dataframe type it'll work appropriately.

    Install dask if this fails.
    """
    schema = pa.DataFrameSchema(
        {
            "year": pa.Column(int, pa.Check(lambda s: s > 2000)),
            "month": pa.Column(str),
            "day": pa.Column(str),
        },
        index=pa.Index(int),
        strict=True,
    )
    from hamilton.function_modifiers import check_output

    @check_output(schema=schema)
    def foo(fail: bool = False) -> dd.DataFrame:
        if fail:
            return dd.from_pandas(
                pd.DataFrame(
                    {
                        "year": ["-2001", "-2002", "-2003"],
                        "month": ["-13", "-6", "120"],
                        "day": ["700", "-156", "367"],
                    }
                ),
                npartitions=1,
            )
        return dd.from_pandas(
            pd.DataFrame(
                {
                    "year": [2001, 2002, 2003],
                    "month": ["3", "6", "12"],
                    "day": ["200", "156", "365"],
                }
            ),
            npartitions=1,
        )

    n = node.Node.from_fn(foo)
    validators = check_output(schema=schema).get_validators(n)
    assert len(validators) == 1
    (validator,) = validators
    result_success = validator.validate(n())  # should not fail
    assert result_success.passes
    result_success = validator.validate(n(True))  # should fail
    assert not result_success.passes


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
@pytest.mark.xfail(
    reason="some weird import issue leads to key error in pandera, can't recreate outside of the series decorator"
)
def test_pandera_decorator_dask_series():
    """Validates that the function can be annotated with a dask series type it'll work appropriately.
    Install dask if this fails.
    """
    schema = pa.SeriesSchema(
        str,
        checks=[
            pa.Check(lambda s: s.str.startswith("foo")),
            pa.Check(lambda s: s.str.endswith("bar")),
            pa.Check(lambda x: len(x) > 3, element_wise=True),
        ],
        nullable=False,
    )
    from hamilton.function_modifiers import check_output

    @check_output(schema=schema)
    def foo(fail: bool = False) -> dd.Series:
        if fail:
            return dd.from_pandas(pd.Series(["xfoobar", "xfoobox", "xfoobaz"]), npartitions=1)
        return dd.from_pandas(pd.Series(["foobar", "foobar", "foobar"]), npartitions=1)

    n = node.Node.from_fn(foo)
    validators = check_output(schema=schema).get_validators(n)
    assert len(validators) == 1
    (validator,) = validators
    result_success = validator.validate(n())  # should not fail
    assert result_success.passes
    result_success = validator.validate(n(True))  # should fail
    assert not result_success.passes
