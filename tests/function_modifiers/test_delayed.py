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

from collections.abc import Callable

import pandas as pd
import pytest

from hamilton import settings
from hamilton.function_modifiers import (
    ResolveAt,
    base,
    extract_columns,
    extract_fields,
    parameterize_sources,
    resolve,
    resolve_from_config,
)

CONFIG_WITH_POWER_MODE_ENABLED = {
    settings.ENABLE_POWER_USER_MODE: True,
}

CONFIG_WITH_POWER_MODE_DISABLED = {
    settings.ENABLE_POWER_USER_MODE: False,
}


@pytest.mark.parametrize(
    ("fn", "required", "optional"),
    [
        (lambda: 1, [], {}),
        (lambda a, b: 1, ["a", "b"], {}),
        (lambda a, b=1: 1, ["a"], {"b": 1}),
        (lambda a=1, b=1: 1, [], {"a": 1, "b": 1}),
    ],
)
def test_extract_and_validate_params_happy(fn: Callable, required: Callable, optional: Callable):
    from hamilton.function_modifiers import delayed

    assert delayed.extract_and_validate_params(fn) == (required, optional)


@pytest.mark.parametrize(
    "fn",
    [
        lambda **kwargs: 1,
        lambda a, b, *args: 1,
        lambda a, b, *args, **kwargs: 1,
    ],
)
def test_extract_and_validate_params_unhappy(fn: Callable):
    from hamilton.function_modifiers import delayed

    with pytest.raises(base.InvalidDecoratorException):
        delayed.extract_and_validate_params(fn)


def test_dynamic_resolves():
    # Note: we use an empty DataFrame for validation only. This test would fail at runtime
    # if we actually tried to execute the DAG because there are no columns "a" or "b" to extract.
    def fn() -> pd.DataFrame:
        return pd.DataFrame()

    decorator = resolve(
        when=ResolveAt.CONFIG_AVAILABLE,
        decorate_with=lambda cols_to_extract: extract_columns(*cols_to_extract),
    )
    decorator_resolved = decorator.resolve(
        {"cols_to_extract": ["a", "b"], **CONFIG_WITH_POWER_MODE_ENABLED}, fn=fn
    )
    # This uses an internal component of extract_columns
    # We may want to add a little more comprehensive testing
    # But for now this will work
    assert decorator_resolved.columns == ("a", "b")


def test_dynamic_resolve_with_configs():
    def fn() -> pd.DataFrame:
        return pd.DataFrame()

    decorator = resolve_from_config(
        decorate_with=lambda cols_to_extract: extract_columns(*cols_to_extract),
    )
    decorator_resolved = decorator.resolve(
        {"cols_to_extract": ["a", "b"], **CONFIG_WITH_POWER_MODE_ENABLED},
        fn=fn,
    )
    # This uses an internal component of extract_columns
    # We may want to add a little more comprehensive testing
    # But for now this will work
    assert decorator_resolved.columns == ("a", "b")


def test_dynamic_resolve_without_power_mode_fails():
    def fn() -> pd.DataFrame:
        return pd.DataFrame()

    decorator = resolve(
        when=ResolveAt.CONFIG_AVAILABLE,
        decorate_with=lambda cols_to_extract: extract_columns(*cols_to_extract),
    )
    with pytest.raises(base.InvalidDecoratorException):
        decorator.resolve(CONFIG_WITH_POWER_MODE_DISABLED, fn=fn)


def test_config_derivation():
    decorator = resolve(
        when=ResolveAt.CONFIG_AVAILABLE,
        decorate_with=lambda cols_to_extract, some_cols_you_might_want_to_extract=[]: (
            extract_columns(*cols_to_extract + some_cols_you_might_want_to_extract)
        ),
    )
    assert decorator.required_config() == ["cols_to_extract"]
    assert decorator.optional_config() == {
        "some_cols_you_might_want_to_extract": [],
    }


def test_delayed_with_optional():
    def fn() -> pd.DataFrame:
        return pd.DataFrame()

    decorator = resolve(
        when=ResolveAt.CONFIG_AVAILABLE,
        decorate_with=lambda cols_to_extract, some_cols_you_might_want_to_extract=["c"]: (
            extract_columns(*cols_to_extract + some_cols_you_might_want_to_extract)
        ),
    )
    resolved = decorator.resolve(
        {"cols_to_extract": ["a", "b"], **CONFIG_WITH_POWER_MODE_ENABLED},
        fn=fn,
    )
    assert list(resolved.columns) == ["a", "b", "c"]
    resolved = decorator.resolve(
        {
            "cols_to_extract": ["a", "b"],
            "some_cols_you_might_want_to_extract": ["d"],
            **CONFIG_WITH_POWER_MODE_ENABLED,
        },
        fn=fn,
    )
    assert list(resolved.columns) == ["a", "b", "d"]


def test_delayed_without_power_mode_fails():
    def fn() -> pd.DataFrame:
        return pd.DataFrame()

    decorator = resolve(
        when=ResolveAt.CONFIG_AVAILABLE,
        decorate_with=lambda cols_to_extract, some_cols_you_might_want_to_extract=["c"]: (
            extract_columns(*cols_to_extract + some_cols_you_might_want_to_extract)
        ),
    )
    with pytest.raises(base.InvalidDecoratorException):
        decorator.resolve(
            {"cols_to_extract": ["a", "b"], **CONFIG_WITH_POWER_MODE_DISABLED},
            fn=fn,
        )


def test_dynamic_resolve_with_extract_fields():
    """Test that @resolve with @extract_fields calls validate() correctly."""

    def fn() -> dict[str, int]:
        return {"a": 1, "b": 2}

    decorator = resolve(
        when=ResolveAt.CONFIG_AVAILABLE,
        decorate_with=lambda fields: extract_fields(fields),
    )
    decorator_resolved = decorator.resolve(
        {"fields": {"a": int, "b": int}, **CONFIG_WITH_POWER_MODE_ENABLED},
        fn=fn,
    )
    assert hasattr(decorator_resolved, "resolved_fields")
    assert decorator_resolved.resolved_fields == {"a": int, "b": int}


def test_resolve_with_parameterize_sources():
    """Test that @resolve with @parameterize_sources calls validate() correctly."""

    def fn(x: int, y: int) -> int:
        return x + y

    decorator = resolve(
        when=ResolveAt.CONFIG_AVAILABLE,
        decorate_with=lambda: parameterize_sources(result_1={"x": "source_x", "y": "source_y"}),
    )
    decorator_resolved = decorator.resolve(
        {**CONFIG_WITH_POWER_MODE_ENABLED},
        fn=fn,
    )
    assert "result_1" in decorator_resolved.parameterization
    mapping = decorator_resolved.parameterization["result_1"]
    assert mapping["x"].source == "source_x"
    assert mapping["y"].source == "source_y"


def test_resolve_from_config_with_extract_fields():
    """Test @resolve_from_config with @extract_fields calls validate() correctly."""

    def fn() -> dict[str, int]:
        return {"a": 1, "b": 2}

    decorator = resolve_from_config(
        decorate_with=lambda fields: extract_fields(fields),
    )
    decorator_resolved = decorator.resolve(
        {"fields": {"a": int, "b": int}, **CONFIG_WITH_POWER_MODE_ENABLED},
        fn=fn,
    )
    assert hasattr(decorator_resolved, "resolved_fields")
    assert decorator_resolved.resolved_fields == {"a": int, "b": int}


def test_resolve_propagates_validate_failure():
    """Test that validate() failures are propagated through resolve."""

    def fn() -> str:
        return "not what you were expecting..."

    decorator = resolve(
        when=ResolveAt.CONFIG_AVAILABLE,
        decorate_with=lambda fields: extract_fields(fields),
    )
    with pytest.raises(base.InvalidDecoratorException):
        decorator.resolve(
            {"fields": {"a": int, "b": int}, **CONFIG_WITH_POWER_MODE_ENABLED},
            fn=fn,
        )


def test_resolve_with_arbitrary_decorator():
    """Test behavior when decorate_with returns something that is not a NodeTransformLifecycle."""

    # NOTE: we want to ensure we don't interfere with other decorators on functions.

    # A decorator that doesn't inherit from NodeTransformLifecycle (but still uses kwargs only)
    class ArbitraryDecorator:
        def __init__(self, a: int, b: int) -> None:
            pass

        def __call__(self, f: Callable) -> Callable:
            return f

    def fn() -> pd.DataFrame:
        return pd.DataFrame()

    decorator = resolve(
        when=ResolveAt.CONFIG_AVAILABLE,
        decorate_with=lambda kwargs: ArbitraryDecorator(**kwargs),
    )
    decorator_resolved = decorator.resolve(
        {"kwargs": {"a": 1, "b": 2}, **CONFIG_WITH_POWER_MODE_ENABLED},
        fn=fn,
    )
    assert isinstance(decorator_resolved, ArbitraryDecorator)
