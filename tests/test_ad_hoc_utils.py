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

import inspect

import pytest

from hamilton import ad_hoc_utils, function_modifiers


def test_copy_func():
    """Tests that we copy the function as intended"""

    @function_modifiers.tag(test_function="true")
    def foo(bar: int) -> int:
        """dummy function"""
        return bar + 1

    cloned_func = ad_hoc_utils._copy_func(foo)

    assert cloned_func.__dict__ == foo.__dict__
    assert cloned_func.__annotations__ == foo.__annotations__

    assert cloned_func is not foo
    assert cloned_func(1) == foo(1)


def test_generate_unique_temp_module_name():
    """Tests that we replace - with _"""
    name = ad_hoc_utils._generate_unique_temp_module_name()
    assert "-" not in name


def test_create_temporary_module():
    """Tests that we create a module with the passed in functions."""

    def bar(baz: int) -> int:
        """dummy function"""
        return baz + 1

    def foo(bar: int) -> int:
        """dummy function"""
        return bar + 1

    def _baz(bar: int) -> int:
        """dummy function, not to be included"""
        return bar + 1

    temp_module = ad_hoc_utils.create_temporary_module(bar, foo)
    expected_members = {
        "__spec__",
        "__loader__",
        "__name__",
        "__doc__",
        "bar",
        "foo",
        "__package__",
    }
    assert set(dict(inspect.getmembers(temp_module)).keys()) == expected_members
    assert "_" in temp_module.__name__
    temp_module_2 = ad_hoc_utils.create_temporary_module(bar, foo, module_name="test_module")
    assert set(dict(inspect.getmembers(temp_module_2)).keys()) == expected_members
    assert temp_module_2.__name__ == "test_module"


def test_create_temporary_module_breaks_helper():
    """Tests that we create a module with the passed in functions."""

    def bar(baz: int) -> int:
        """dummy function"""
        return baz + 1

    def foo(bar: int) -> int:
        """dummy function"""
        return bar + 1

    def _baz(bar: int) -> int:
        """dummy function, not to be included"""
        return bar + 1

    with pytest.raises(ValueError):
        ad_hoc_utils.create_temporary_module(bar, foo, _baz)


def test_inspect_module_from_source():
    source = '''
def bar(baz: int) -> int:
    """dummy function"""
    return baz + 1

def foo(bar: int) -> int:
    """dummy function"""
    return bar + 1

def _baz(bar: int) -> int:
    """dummy function, not to be included"""
    return bar + 1
'''
    module = ad_hoc_utils.module_from_source(source)

    try:
        inspect.getsource(module.bar)
    except OSError as e:
        assert False, f"module improperly added to linecache. {e}"  # noqa
