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

"""Due to the recursive nature of hashing of sequences, mappings, and other
complex types, many tests are not "true" unit tests. The base cases are
the original `hash_value()` and the `hash_primitive()` functions.
"""

import numpy as np
import pandas as pd
import pytest

from hamilton.caching import fingerprinting


def test_hash_none():
    fingerprint = fingerprinting.hash_value(None)
    assert fingerprint == "<none>"


def test_hash_no_dict_attribute():
    """Classes without a __dict__ attribute can't be hashed.
    during the base case.
    """

    class Foo:
        __slots__ = ()

    obj = Foo()
    assert not hasattr(obj, "__dict__")

    fingerprint = fingerprinting.hash_value(obj)

    assert fingerprint == fingerprinting.UNHASHABLE


def test_empty_dict_attr_is_unhashable():
    """Classes with an empty __dict__ can't be hashed during the base case."""

    class Foo: ...  # noqa: E701

    obj = Foo()
    assert obj.__dict__ == {}

    fingerprint = fingerprinting.hash_value(obj)

    assert fingerprint == fingerprinting.UNHASHABLE


def test_hash_recursively():
    """Classes without a specialized hash function are hashed recursively
    via their __dict__ attribute.
    """

    class Foo:
        def __init__(self, obj):
            self.foo = "foo"
            self.obj = obj

    foo0 = Foo(obj=None)
    foo1 = Foo(obj=foo0)
    foo2 = Foo(obj=foo1)

    foo0_dict = {"foo": "foo", "obj": None}
    foo1_dict = {"foo": "foo", "obj": foo0_dict}
    foo2_dict = {"foo": "foo", "obj": foo1_dict}

    assert foo0.__dict__ == foo0_dict
    # NOTE foo2.__dict__ != foo2_dict, because foo2.__dict__ holds
    # a reference to the object foo1, which is not the case for foo2_dict

    fingerprint0 = fingerprinting.hash_value(foo0)
    assert fingerprint0 == fingerprinting.hash_value(foo0_dict)

    fingerprint1 = fingerprinting.hash_value(foo1)
    assert fingerprint1 == fingerprinting.hash_value(foo1_dict)

    fingerprint2 = fingerprinting.hash_value(foo2)
    assert fingerprint2 == fingerprinting.hash_value(foo2_dict)


def test_max_recursion_depth():
    """Set the max recursion depth to 0 to prevent any recursion.
    After max depth, the default case should return UNHASHABLE.
    """

    class Foo:
        def __init__(self, obj):
            self.foo = "foo"
            self.obj = obj

    foo0 = Foo(obj=None)
    foo1 = Foo(obj=foo0)
    foo2 = Foo(obj=foo1)

    foo0_dict = {"foo": "foo", "obj": None}
    assert foo0.__dict__ == foo0_dict

    fingerprint0 = fingerprinting.hash_value(foo0)
    assert fingerprint0 == fingerprinting.hash_value(foo0_dict)

    fingerprinting.set_max_depth(1)
    # equivalent after reaching max depth
    fingerprint1 = fingerprinting.hash_value(foo1)
    fingerprint2 = fingerprinting.hash_value(foo2)
    assert fingerprint1 == fingerprint2

    fingerprinting.set_max_depth(2)
    # no longer equivalent after increasing max depth
    fingerprint1 = fingerprinting.hash_value(foo1)
    fingerprint2 = fingerprinting.hash_value(foo2)
    assert fingerprint1 != fingerprint2


@pytest.mark.parametrize(
    "obj,expected_hash",
    [
        ("hello-world", "IJUxIYl1PeatR9_iDL6X7A=="),
        (17.31231, "vAYX8MD8yEHK6dwnIPVUaw=="),
        (16474, "L_epMRRUy3Qq5foVvFT_OQ=="),
        (True, "-CfPRi9ihI3zfF4elKTadA=="),
        (b"\x951!\x89u=\xe6\xadG\xdf", "qK2VJ0vVTRJemfC0beO8iA=="),
    ],
)
def test_hash_primitive(obj, expected_hash):
    fingerprint = fingerprinting.hash_primitive(obj)
    assert fingerprint == expected_hash


@pytest.mark.parametrize(
    "obj,expected_hash",
    [
        ([0, True, "hello-world"], "Pg9LP3Y-8yYsoWLXedPVKDwTAa7W8_fjJNTTUA=="),
        ((17.0, False, "world"), "wyuuKMuL8rp53_CdYAtyMmyetnTJ9LzmexhJrQ=="),
    ],
)
def test_hash_sequence(obj, expected_hash):
    fingerprint = fingerprinting.hash_sequence(obj)
    assert fingerprint == expected_hash


def test_hash_equals_for_different_sequence_types():
    list_obj = [0, True, "hello-world"]
    tuple_obj = (0, True, "hello-world")
    expected_hash = "Pg9LP3Y-8yYsoWLXedPVKDwTAa7W8_fjJNTTUA=="

    list_fingerprint = fingerprinting.hash_sequence(list_obj)
    tuple_fingerprint = fingerprinting.hash_sequence(tuple_obj)
    assert list_fingerprint == tuple_fingerprint == expected_hash


def test_hash_ordered_mapping():
    obj = {0: True, "key": "value", 17.0: None}
    expected_hash = "1zH9TfTu0-nlWXXXYo0vigFFSQajWXov2w4AZQ=="
    fingerprint = fingerprinting.hash_mapping(obj, ignore_order=False)
    assert fingerprint == expected_hash


def test_hash_mapping_where_order_matters():
    obj1 = {0: True, "key": "value", 17.0: None}
    obj2 = {"key": "value", 17.0: None, 0: True}
    fingerprint1 = fingerprinting.hash_mapping(obj1, ignore_order=False)
    fingerprint2 = fingerprinting.hash_mapping(obj2, ignore_order=False)
    assert fingerprint1 != fingerprint2


def test_hash_unordered_mapping():
    obj = {0: True, "key": "value", 17.0: None}
    expected_hash = "uw0dfSAEgE9nOK3bHgmJ4TR3-VFRqOAoogdRmw=="
    fingerprint = fingerprinting.hash_mapping(obj, ignore_order=True)
    assert fingerprint == expected_hash


def test_hash_mapping_where_order_doesnt_matter():
    obj1 = {0: True, "key": "value", 17.0: None}
    obj2 = {"key": "value", 17.0: None, 0: True}
    fingerprint1 = fingerprinting.hash_mapping(obj1, ignore_order=True)
    fingerprint2 = fingerprinting.hash_mapping(obj2, ignore_order=True)
    assert fingerprint1 == fingerprint2


def test_hash_set():
    obj = {0, True, "key", "value", 17.0, None}
    expected_hash = "dKyAE-ob4_GD-Mb5Lu2R-VJAxGctY4L8JDwc2g=="
    fingerprint = fingerprinting.hash_set(obj)
    assert fingerprint == expected_hash


def test_hash_pandas():
    """pandas has a specialized hash function"""
    obj = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    expected_hash = "LSHACWyG83JBIggxO9LGrerW3WZEy4nUOmIQoA=="
    fingerprint = fingerprinting.hash_pandas_obj(obj)
    assert fingerprint == expected_hash


def test_hash_numpy():
    array = np.array([[0, 1], [2, 3]])
    expected_hash = "ZwjDgY0zQOxO9KPHlYecog=="
    fingerprint = fingerprinting.hash_value(array)
    assert fingerprint == expected_hash
