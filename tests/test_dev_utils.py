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

import operator

import pytest

from hamilton.dev_utils.deprecation import DeprecationError, Version, deprecated


@pytest.mark.parametrize(
    ("version_1", "version_2", "op"),
    [
        (Version(0, 1, 2), Version(0, 1, 2), operator.eq),
        (Version(0, 1, 2), Version(0, 1, 3), operator.lt),
        (Version(0, 1, 2), Version(0, 1, 1), operator.gt),
        (Version(1, 9, 0), Version(2, 0, 0), operator.lt),
        (Version(2, 0, 0), Version(1, 9, 0), operator.gt),
    ],
)
def test_version_compare(version_1, version_2, op):
    assert op(version_1, version_2)


@pytest.mark.parametrize(
    ("version_tuple", "version"),
    [((0, 1, 2), Version(0, 1, 2)), ((0, 1, 2, "rc1"), Version(0, 1, 2))],
)
def test_from_version_tuple(version_tuple, version):
    assert Version.from_version_tuple(version_tuple) == version


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(
            warn_starting=(0, 0, 0),
            fail_starting=(0, 0, 1),
            use_this=None,
            explanation="something",
            migration_guide="https://github.com/apache/hamilton",
        ),
        dict(
            warn_starting=(0, 0, 0),
            fail_starting=(0, 0, 1),
            use_this=test_version_compare,
            explanation="something",
            migration_guide=None,
        ),
        dict(
            warn_starting=(0, 0, 0),
            fail_starting=(1, 0, 0),
            use_this=test_version_compare,
            explanation="something",
            migration_guide=None,
        ),
    ],
)
def test_validate_deprecated_decorator_params_happy(kwargs):
    deprecated(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(
            warn_starting=(1, 0, 0),
            fail_starting=(0, 0, 1),
            use_this=None,
            explanation="something",
            migration_guide="https://github.com/apache/hamilton",
        ),
        dict(
            warn_starting=(0, 0, 0),
            fail_starting=(0, 0, 1),
            use_this=None,
            explanation="something",
            migration_guide=None,
        ),
        dict(
            warn_starting=(0, 0, 0),
            fail_starting=(1, 0, 0),
            use_this=None,
            explanation="something",
            migration_guide=None,
        ),
    ],
)
def test_validate_deprecated_decorator_params_sad(kwargs):
    with pytest.raises(ValueError):
        deprecated(**kwargs)


def test_call_function_not_deprecated_yet():
    warned = False

    def warn(s):
        nonlocal warned
        warned = True

    def replacement_function() -> bool:
        return True

    @deprecated(
        warn_starting=(0, 5, 0),
        fail_starting=(1, 0, 0),
        use_this=replacement_function,
        explanation="True is the new False",
        migration_guide="https://github.com/apache/hamilton",
        current_version=(0, 0, 0),
        warn_action=warn,
    )
    def deprecated_function() -> bool:
        return False

    deprecated_function()
    assert not warned


def test_call_function_soon_to_be_deprecated():
    warned = False

    def warn(s):
        nonlocal warned
        warned = True

    def replacement_function() -> bool:
        return True

    @deprecated(
        warn_starting=(0, 5, 0),
        fail_starting=(1, 0, 0),
        use_this=replacement_function,
        explanation="True is the new False",
        migration_guide="https://github.com/apache/hamilton",
        current_version=(0, 6, 0),
        warn_action=warn,
    )
    def deprecated_function() -> bool:
        return False

    deprecated_function()
    assert warned


def test_call_function_already_deprecated():
    def replacement_function() -> bool:
        return True

    @deprecated(
        warn_starting=(0, 5, 0),
        fail_starting=(1, 0, 0),
        use_this=replacement_function,
        explanation="True is the new False",
        migration_guide="https://github.com/apache/hamilton",
        current_version=(1, 1, 0),
    )
    def deprecated_function():
        return False

    with pytest.raises(DeprecationError):
        deprecated_function()


def test_call_function_class_not_deprecated_yet():
    warned = False

    def warn(s):
        nonlocal warned
        warned = True

    def replacement_function() -> bool:
        return True

    @deprecated(
        warn_starting=(0, 5, 0),
        fail_starting=(1, 0, 0),
        use_this=replacement_function,
        explanation="True is the new False",
        migration_guide="https://github.com/apache/hamilton",
        current_version=(0, 0, 0),
        warn_action=warn,
    )
    class deprecated_function:
        def __call__(self):
            return False

    deprecated_function()
    assert not warned


def test_call_function_class_soon_to_be_deprecated():
    warned = False

    def warn(s):
        nonlocal warned
        warned = True

    def replacement_function() -> bool:
        return True

    @deprecated(
        warn_starting=(0, 5, 0),
        fail_starting=(1, 0, 0),
        use_this=replacement_function,
        explanation="True is the new False",
        migration_guide="https://github.com/apache/hamilton",
        current_version=(0, 6, 0),
        warn_action=warn,
    )
    class deprecated_function:
        def __call__(self):
            return False

    deprecated_function()()
    assert warned


def test_call_function_class_already_deprecated():
    def replacement_function() -> bool:
        return True

    @deprecated(
        warn_starting=(0, 5, 0),
        fail_starting=(1, 0, 0),
        use_this=replacement_function,
        explanation="True is the new False",
        migration_guide="https://github.com/apache/hamilton",
        current_version=(1, 1, 0),
    )
    class deprecated_function:
        def __call__(self):
            return False

    with pytest.raises(DeprecationError):
        deprecated_function()()


def _decorate_function(decorator: deprecated):
    @decorator
    def deprecated_function() -> bool:
        return False

    return deprecated_function


def _decorate_class(decorator: deprecated):
    @decorator
    class DeprecatedCallable:
        def __call__(self) -> bool:
            return False

    return DeprecatedCallable()


# The first schedule has the shape every real deprecation uses: fail_starting is a major release, so
# "just below" it is the previous major's latest minor.
@pytest.mark.parametrize(
    ("warn_starting", "fail_starting", "current_version", "expected"),
    [
        pytest.param((1, 89, 0), (2, 0, 0), (1, 88, 9), "none", id="below-warn"),
        pytest.param((1, 89, 0), (2, 0, 0), (1, 89, 0), "warn", id="at-warn"),
        pytest.param((1, 89, 0), (2, 0, 0), (1, 89, 1), "warn", id="above-warn"),
        pytest.param((1, 89, 0), (2, 0, 0), (1, 90, 0), "warn", id="below-major-fail"),
        pytest.param((1, 89, 0), (2, 0, 0), (2, 0, 0), "fail", id="at-major-fail"),
        pytest.param((1, 89, 0), (2, 0, 0), (2, 0, 1), "fail", id="above-major-fail"),
        pytest.param((0, 5, 3), (0, 7, 2), (0, 5, 2), "none", id="below-patch-warn"),
        pytest.param((0, 5, 3), (0, 7, 2), (0, 5, 3), "warn", id="at-patch-warn"),
        pytest.param((0, 5, 3), (0, 7, 2), (0, 5, 4), "warn", id="above-patch-warn"),
        pytest.param((0, 5, 3), (0, 7, 2), (0, 7, 1), "warn", id="below-patch-fail"),
        pytest.param((0, 5, 3), (0, 7, 2), (0, 7, 2), "fail", id="at-patch-fail"),
        pytest.param((0, 5, 3), (0, 7, 2), (0, 7, 3), "fail", id="above-patch-fail"),
    ],
)
@pytest.mark.parametrize(
    "decorate", [_decorate_function, _decorate_class], ids=["function", "class"]
)
def test_deprecation_boundaries_are_inclusive(
    warn_starting, fail_starting, current_version, expected, decorate
):
    warnings, failures = [], []
    deprecated_callable = decorate(
        deprecated(
            warn_starting=warn_starting,
            fail_starting=fail_starting,
            use_this=None,
            explanation="something",
            migration_guide="https://github.com/apache/hamilton",
            current_version=current_version,
            warn_action=warnings.append,
            fail_action=failures.append,
        )
    )

    deprecated_callable()

    actual = "fail" if failures else "warn" if warnings else "none"
    assert actual == expected
    assert len(warnings) + len(failures) <= 1
