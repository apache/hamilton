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

from typing import Callable

import pytest

from hamilton import settings
from hamilton.function_modifiers import (
    ResolveAt,
    base,
    extract_columns,
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
    "fn,required,optional",
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
    decorator = resolve(
        when=ResolveAt.CONFIG_AVAILABLE,
        decorate_with=lambda cols_to_extract: extract_columns(*cols_to_extract),
    )
    decorator_resolved = decorator.resolve(
        {"cols_to_extract": ["a", "b"], **CONFIG_WITH_POWER_MODE_ENABLED}, fn=test_dynamic_resolves
    )
    # This uses an internal component of extract_columns
    # We may want to add a little more comprehensive testing
    # But for now this will work
    assert decorator_resolved.columns == ("a", "b")


def test_dynamic_resolve_with_configs():
    decorator = resolve_from_config(
        decorate_with=lambda cols_to_extract: extract_columns(*cols_to_extract),
    )
    decorator_resolved = decorator.resolve(
        {"cols_to_extract": ["a", "b"], **CONFIG_WITH_POWER_MODE_ENABLED}, fn=test_dynamic_resolves
    )
    # This uses an internal component of extract_columns
    # We may want to add a little more comprehensive testing
    # But for now this will work
    assert decorator_resolved.columns == ("a", "b")


def test_dynamic_fails_without_power_mode_fails():
    decorator = resolve(
        when=ResolveAt.CONFIG_AVAILABLE,
        decorate_with=lambda cols_to_extract: extract_columns(*cols_to_extract),
    )
    with pytest.raises(base.InvalidDecoratorException):
        decorator_resolved = decorator.resolve(
            CONFIG_WITH_POWER_MODE_DISABLED, fn=test_dynamic_fails_without_power_mode_fails
        )
        # This uses an internal component of extract_columns
        # We may want to add a little more comprehensive testing
        # But for now this will work
        assert decorator_resolved.columns == ("a", "b")


def test_config_derivation():
    decorator = resolve(
        when=ResolveAt.CONFIG_AVAILABLE,
        decorate_with=lambda cols_to_extract,
        some_cols_you_might_want_to_extract=[]: extract_columns(
            *cols_to_extract + some_cols_you_might_want_to_extract
        ),
    )
    assert decorator.required_config() == ["cols_to_extract"]
    assert decorator.optional_config() == {
        "some_cols_you_might_want_to_extract": [],
    }


def test_delayed_with_optional():
    decorator = resolve(
        when=ResolveAt.CONFIG_AVAILABLE,
        decorate_with=lambda cols_to_extract,
        some_cols_you_might_want_to_extract=["c"]: extract_columns(
            *cols_to_extract + some_cols_you_might_want_to_extract
        ),
    )
    resolved = decorator.resolve(
        {"cols_to_extract": ["a", "b"], **CONFIG_WITH_POWER_MODE_ENABLED},
        fn=test_delayed_with_optional,
    )
    assert list(resolved.columns) == ["a", "b", "c"]
    resolved = decorator.resolve(
        {
            "cols_to_extract": ["a", "b"],
            "some_cols_you_might_want_to_extract": ["d"],
            **CONFIG_WITH_POWER_MODE_ENABLED,
        },
        fn=test_delayed_with_optional,
    )
    assert list(resolved.columns) == ["a", "b", "d"]


def test_delayed_without_power_mode_fails():
    decorator = resolve(
        when=ResolveAt.CONFIG_AVAILABLE,
        decorate_with=lambda cols_to_extract,
        some_cols_you_might_want_to_extract=["c"]: extract_columns(
            *cols_to_extract + some_cols_you_might_want_to_extract
        ),
    )
    with pytest.raises(base.InvalidDecoratorException):
        decorator.resolve(
            {"cols_to_extract": ["a", "b"], **CONFIG_WITH_POWER_MODE_DISABLED},
            fn=test_delayed_with_optional,
        )
