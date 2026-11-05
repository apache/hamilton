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

"""How Hamilton's own deprecations reach users: on the release clock, as warnings users can filter."""

import warnings

import pytest

from hamilton.dev_utils.deprecation import deprecated


def _decorated_function(**overrides):
    arguments = dict(
        warn_starting=(1, 0, 0),
        fail_starting=(2, 0, 0),
        use_this=None,
        explanation="Use the new one.",
        migration_guide="https://example.com/guide",
        current_version=(1, 5, 0),
    )

    @deprecated(**{**arguments, **overrides})
    def old_api() -> str:
        return "result"

    return old_api


def _decorated_class(**overrides):
    arguments = dict(
        warn_starting=(1, 0, 0),
        fail_starting=(2, 0, 0),
        use_this=None,
        explanation="Use the new one.",
        migration_guide="https://example.com/guide",
        current_version=(1, 5, 0),
    )

    @deprecated(**{**arguments, **overrides})
    class OldDecorator:
        def __call__(self) -> str:
            return "result"

    return lambda: OldDecorator()()


@pytest.mark.parametrize(
    "decorate", [_decorated_function, _decorated_class], ids=["function", "class"]
)
def test_deprecation_warns_with_a_future_warning_at_the_calling_line(decorate):
    old_api = decorate()
    with pytest.warns(
        FutureWarning, match="will be deprecated by hamilton version: 2.0.0"
    ) as record:
        assert old_api() == "result"
    assert len(record) == 1
    assert record[0].filename == __file__


@pytest.mark.parametrize(
    "decorate", [_decorated_function, _decorated_class], ids=["function", "class"]
)
def test_deprecation_warning_follows_the_warning_filters(decorate):
    old_api = decorate()
    with warnings.catch_warnings():
        warnings.simplefilter("error", FutureWarning)
        with pytest.raises(FutureWarning):
            old_api()
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("ignore", FutureWarning)
        assert old_api() == "result"
    assert record == []


@pytest.mark.parametrize(
    "decorate", [_decorated_function, _decorated_class], ids=["function", "class"]
)
def test_custom_warn_action_replaces_the_warning(decorate):
    messages = []
    old_api = decorate(warn_action=messages.append)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert old_api() == "result"
    assert len(messages) == 1
